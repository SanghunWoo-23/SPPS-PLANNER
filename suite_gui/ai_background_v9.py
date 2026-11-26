"""Non-blocking, single-flight operations for the V9 Excel/AI Tk dialog.

Workers never call Tk APIs; all callbacks execute through Tk.after on the UI thread.
A closed window discards results. Closing a window cannot forcibly terminate an
in-flight sklearn fit, but it cannot update destroyed widgets either.
"""
from __future__ import annotations

from queue import Empty, SimpleQueue
from threading import Thread, Lock
import gc
import multiprocessing as mp
from pathlib import Path
from typing import Any, Callable


# Tcl/Tk objects must not be garbage-collected from an Excel I/O worker thread.
# CPython 3.13 can abort if a previous destroyed Tk dialog is finalized there.
# Bound GC suppression to the lifetime of active I/O workers; never disable
# garbage collection for the entire application.
_ACTIVE_IO_WORKERS=0
_WORKERS_LOCK=Lock()
_REENABLE_GC=False


def _begin_background_io():
    global _ACTIVE_IO_WORKERS, _REENABLE_GC
    with _WORKERS_LOCK:
        if _ACTIVE_IO_WORKERS==0:
            if gc.isenabled():
                # Called on the Tk thread, so old Tcl objects finalize safely.
                gc.collect()
                gc.disable()
                _REENABLE_GC=True
            else:
                _REENABLE_GC=False
        _ACTIVE_IO_WORKERS+=1


def _end_background_io():
    global _ACTIVE_IO_WORKERS, _REENABLE_GC
    with _WORKERS_LOCK:
        _ACTIVE_IO_WORKERS=max(0,_ACTIVE_IO_WORKERS-1)
        if _ACTIVE_IO_WORKERS==0 and _REENABLE_GC:
            gc.enable()
            _REENABLE_GC=False


class UiBackgroundRunner:
    def __init__(self, window: Any, busy_changed: Callable[[bool], None], *, poll_ms: int = 40):
        self._window = window
        self._busy_changed = busy_changed
        self._poll_ms = poll_ms
        self._queue: SimpleQueue[tuple[bool, Any]] = SimpleQueue()
        self.busy = False
        self.closed = False
        self._process = None
        self._process_queue = None

    def submit(self, compute: Callable[[], Any], success: Callable[[Any], None],
               failure: Callable[[Exception], None]) -> bool:
        if self.closed or self.busy:
            return False
        self.busy = True
        self._busy_changed(True)
        _begin_background_io()

        def worker():
            try:
                try:
                    self._queue.put((True, compute()))
                except Exception as exc:
                    self._queue.put((False, exc))
            finally:
                _end_background_io()

        try:
            Thread(target=worker, daemon=True, name='SPPS-V9-AI-worker').start()
        except Exception:
            _end_background_io()
            self.busy=False
            self._busy_changed(False)
            raise

        def poll():
            if self.closed:
                return
            try:
                ok, result = self._queue.get_nowait()
            except Empty:
                self._window.after(self._poll_ms, poll)
                return
            self.busy = False
            self._busy_changed(False)
            if self.closed:
                return
            try:
                (success if ok else failure)(result)
            except Exception as exc:
                # UI callback failure must not leave controls permanently disabled.
                failure(exc)

        self._window.after(self._poll_ms, poll)
        return True

    def submit_training_process(self, kind: str, data_dir, model_dir, target,
                                success: Callable[[Any], None],
                                failure: Callable[[Exception], None]) -> bool:
        """Train in a killable process, so Cancel actually stops CPU-heavy ML.

        Spawn is used on Windows and POSIX to avoid forking an active Tk UI.
        This path supports only whitelisted built-in training operations.
        """
        if kind not in ('linear','stage'):
            raise ValueError('Unknown isolated training task.')
        if self.busy or self.closed:
            return False
        self.busy=True
        self._busy_changed(True)
        try:
            ctx=mp.get_context('spawn')
            result_queue=ctx.Queue(maxsize=1)
            process=ctx.Process(target=_training_process_entry,
                 args=(result_queue,kind,str(data_dir),str(model_dir),target),
                 daemon=True,name='SPPS-V9-AI-train')
            process.start()
            self._process=process
            self._process_queue=result_queue
            self._busy_changed(True)
        except (OSError, RuntimeError, ValueError) as exc:
            self.busy=False
            self._busy_changed(False)
            failure(exc)
            return False

        def poll():
            if self.closed or self._process is not process:
                return
            try:
                ok,value=result_queue.get_nowait()
            except Empty:
                if process.is_alive():
                    self._window.after(self._poll_ms,poll)
                    return
                # A crashed child can be reported without blocking the UI.
                if process.exitcode is None:
                    self._window.after(self._poll_ms,poll)
                    return
                ok,value=False,f'AI training process ended unexpectedly (exit {process.exitcode}).'
            self._process=None
            self._process_queue=None
            process.join(timeout=0)
            try:result_queue.close()
            except (OSError,ValueError):pass
            self.busy=False
            self._busy_changed(False)
            if self.closed:return
            if ok: success(value)
            else: failure(ValueError(str(value)[:600]))

        self._window.after(self._poll_ms,poll)
        return True

    def cancel_training(self) -> bool:
        """Hard-stop only the isolated process, never the currently running UI thread."""
        child=self._process
        if child is None or not self.busy:
            return False
        self._process=None
        queue=self._process_queue
        self._process_queue=None
        if child.is_alive():
            child.terminate()
        child.join(timeout=1)
        if child.is_alive():
            child.kill()
            child.join(timeout=1)
        if queue is not None:
            try:queue.close()
            except (OSError,ValueError):pass
        self.busy=False
        if not self.closed:self._busy_changed(False)
        return True

    def close(self):
        self.cancel_training()
        self.closed = True
        self._window.destroy()


def _training_process_entry(queue, kind, data_dir, model_dir, target):
    """Top-level spawn entry; no Tk imports or user-supplied Python code."""
    try:
        from suite_gui.ai_excel_core_v9 import load_reviewed_dataset,train_local_advisor
        frame,metadata=load_reviewed_dataset(Path(data_dir))
        # Limit unbounded memory pressure before constructing an ensemble.
        try:
            import psutil
            if psutil.virtual_memory().available < 350*1024*1024:
                raise MemoryError('Insufficient free RAM to start AI training safely.')
        except ImportError:
            pass
        if kind=='linear':
            result=train_local_advisor(frame,target,Path(model_dir),metadata['dataset_sha256'])
        elif kind=='stage':
            from suite_gui.process_ai_v9 import train_partitioned_stage_advisors
            result=train_partitioned_stage_advisors(frame,target,Path(model_dir),metadata['dataset_sha256'])
        else:
            raise ValueError('Unrecognized process task')
        queue.put((True,result))
    except Exception as exc:
        queue.put((False,f'{type(exc).__name__}: {str(exc)[:500]}'))

