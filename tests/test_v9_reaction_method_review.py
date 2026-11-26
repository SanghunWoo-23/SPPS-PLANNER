"""V9.0.0 reaction method editor and head-to-tail protective precursor QA."""
import json
import pytest
from spps_planner.reaction_planner_v9 import (
    prepare_reaction_review, ReactionPlanError, method_choices, REACTION_METHODS
)
from spps_planner.mass_balance_v9 import calculate_mass_states
from suite_gui.auto_plan_option_v9 import build_review_draft
from suite_gui.checklist_mass_v9 import add_process_stages


def test_supported_methods_have_distinct_reagent_roles():
    assert len(method_choices()) >= 4
    assert REACTION_METHODS['DIC_HOBT']['reagents'] == [('DIC','coupling_reagent'),('HOBt','additive')]
    assert REACTION_METHODS['PYBOP_NMM']['reagents'][1] == ('NMM','base')
    assert all(role != 'catalyst' for name,role in REACTION_METHODS['HATU_DIEA']['reagents'])


def test_millimolar_solution_quantity_per_copy_and_total():
    r=prepare_reaction_review('dS-dV-dS','2-CTC',scale_mmol=.2,copies=3,
            method_id='EDC_HOBT',concentration_mm=1.0,solvent='DMF',reaction_time_h=36.,
            equivalents={'EDC·HCl':3.,'HOBt':3.})
    assert r['volume_per_copy_ml']==pytest.approx(200)
    assert r['volume_total_ml']==pytest.approx(600)
    assert r['reagents'][0]['mmol_per_copy']==pytest.approx(.6)
    assert r['reagents'][0]['mmol_total']==pytest.approx(1.8)
    assert r['reagents'][1]['role']=='additive'
    assert r['method_status']=='OPERATOR_SUPPLIED_REVIEW_REQUIRED'
    assert r['approval']=='DRAFT_NOT_APPROVED'
    mass=calculate_mass_states('dS-dV-dS','2-CTC')
    assert r['protected_cyclic_mw']==mass['head_to_tail_protected_mw']
    assert r['protected_linear_mw']==mass['selective_cleavage_mw']
    json.dumps(r,allow_nan=False)


def test_missing_values_never_inferred():
    r=prepare_reaction_review('SGS','2-CTC',scale_mmol=.1)
    assert r['method_status']=='INCOMPLETE_REVIEW_ONLY'
    assert r['volume_per_copy_ml'] is None
    assert all(i['mmol_per_copy'] is None for i in r['reagents'])
    assert any('INCOMPLETE METHOD' in s for s in r['warnings'])


@pytest.mark.parametrize('kwargs',[
    {'reaction_type':'disulfide'},
    {'reaction_type':'cuaac'},
    {'phase':'on_resin'},
    {'method_id':'UNKNOWN'},
    {'concentration_mm':'NaN'},
    {'concentration_mm':0},
    {'copies':1.5},
    {'equivalents':{'DIC':3.,'HOBt':-1}},
    {'equivalents':{'DIC':3.,'HOBt':2.,'DIEA':1}},
    {'temperature_c':'inf'},
])
def test_unsupported_or_invalid_conditions_fail_closed(kwargs):
    with pytest.raises(ReactionPlanError):
        prepare_reaction_review('dS-dV-dS','2-CTC',scale_mmol=.1,**kwargs)

@pytest.mark.parametrize('seq,resin',[
    ('SGS','Rink Amide AM'), ('Ac-SGS','2-CTC'),('SGS-NH2','2-CTC'),
    ('K(GGEP)','2-CTC'),('S(UnknownProtection)-V-S','2-CTC'),
])
def test_blocked_or_unknown_molecules_no_false_method(seq,resin):
    with pytest.raises((ReactionPlanError,ValueError)):
        prepare_reaction_review(seq,resin,scale_mmol=.1)


def test_draft_export_and_checklist_remain_review_only():
    r=prepare_reaction_review('dS-dV-dS','2-CTC',scale_mmol=.1,
        concentration_mm=1.,solvent='DMF',reaction_time_h=24.,
        equivalents={'DIC':3.,'HOBt':3.})
    draft=build_review_draft('dS-dV-dS',.1,'2-CTC',.8,'DIC/HOBt',1,
             product_path='head_to_tail_protected',reaction_review=r)
    assert draft['reaction_review']['system_id']=='DIC_HOBT'
    assert draft['status']=='DRAFT_NOT_APPROVED'
    assert draft['cleavage']['cocktail'] is None
    checklist=[]
    add_process_stages(checklist,calculate_mass_states('dS-dV-dS','2-CTC'),
       {'product_path':'head_to_tail_protected','reaction_review':r})
    assert len(checklist)==2
    assert 'DIC / HOBt' in checklist[-1]['note']
    assert 'NOT APPROVED' in checklist[-1]['note']
    assert float(checklist[-1]['peptide_mw'])==pytest.approx(r['protected_cyclic_mw'])


def test_stale_mass_reaction_not_reused_in_checklist():
    r=prepare_reaction_review('dS-dV-dS','2-CTC',scale_mmol=.1)
    checklist=[]
    add_process_stages(checklist,calculate_mass_states('SGS','2-CTC'),
       {'product_path':'head_to_tail_protected','reaction_review':r})
    assert 'STALE METHOD' in checklist[-1]['note']


def test_selective_cleavage_1_5_percent_default_and_volume_accounting():
    from spps_planner.reaction_planner_v9 import prepare_selective_cleavage_review
    review=prepare_selective_cleavage_review(resin='2-CTC',total_volume_ml='80',contact_time_min='20')
    assert review['system_label']=='1.5% TFA / DCM'
    assert review['tfa_volume_ml']==pytest.approx(1.2)
    assert review['dcm_volume_ml']==pytest.approx(78.8)
    assert review['status']=='DRAFT_NOT_APPROVED'
    assert prepare_selective_cleavage_review(resin='Rink Amide AM')['status']=='RESIN_COMPATIBILITY_REVIEW_REQUIRED'
    assert prepare_selective_cleavage_review(method_id='HFIP_DCM')['tfa_volume_ml'] is None
    with pytest.raises(ReactionPlanError):
        prepare_selective_cleavage_review(resin='2-CTC',total_volume_ml='nan')


def test_branch_coupling_system_is_separate_from_main_chain():
    from spps_planner.reaction_planner_v9 import prepare_branch_coupling_review
    from suite_gui.modules.add_peptide_dialog import build_item_payload, _dialog_values_from_item
    from types import SimpleNamespace
    values=dict(project='QA',peptide='Br',sequence='AKG',scale='0.2',copies='1',
        resin='2-CTC',loading='0.8',reagent='DIC',additive='HOBt (anhydrous)',
        base='',solvent='DMF',preset='Custom',synthesis_form='branched',branch_point='K2',
        branch_arm='RG',branch_pg='Dde',branch_coupling_system='HBTU_NMM',
        branch_primary_eq='3',branch_secondary_eq='6',branch_coupling_solvent='DMF',
        selective_cleavage_system='TFA_DCM_1_5',selective_time_min='20',selective_total_volume_ml='80')
    item=build_item_payload(SimpleNamespace(),values)
    assert item['default_reagent']=='DIC'
    assert [r['name'] for r in item['branch_coupling_review']['reagents']]==['HBTU','NMM']
    assert [r['equivalents'] for r in item['branch_coupling_review']['reagents']]==[3.,6.]
    assert 'selective_cleavage_review' not in item  # Only head-to-tail uses mild resin cleavage
    assert item['branch_boc_review']['reagents'][0]['equivalents']==3
    assert item['global_cleavage_review']['system_id']=='TFA_TIS_WATER_95'
    restored=_dialog_values_from_item(item)
    assert restored['branch_coupling_system']=='HBTU_NMM'
    assert restored['branch_primary_eq']=='3.0'
    with pytest.raises(ReactionPlanError):
        prepare_branch_coupling_review('HBTU_NMM',equivalents={'HBTU':-2})


def test_hbtu_nmm_head_to_tail_editor_engine_support():
    review=prepare_reaction_review('SVS','2-CTC',scale_mmol=0.1,
        method_id='HBTU_NMM',equivalents={'HBTU':'3','NMM':'6'},
        solvent='DMF',reaction_time_h='2',concentration_mm='1')
    assert review['system_id']=='HBTU_NMM'
    assert review['reagents'][1]['role']=='base'
    assert review['reagents'][0]['mmol_per_copy']==pytest.approx(.3)
    assert review['volume_per_copy_ml']==pytest.approx(100)
    assert review['approval']=='DRAFT_NOT_APPROVED'


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'), reason='Requires GUI display')
@pytest.mark.parametrize('kind', ['branched', 'cyclic'])
def test_operator_methods_are_linked_to_generated_plan_and_excel(tmp_path, monkeypatch, kind):
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from suite_gui.modules import plan_workflow
    import pandas as pd
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:None)
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    values=dict(project='QA',peptide='Audit',sequence='AKG' if kind=='branched' else 'SVS',
        scale='0.2',copies='1',resin='2-CTC',loading='0.8',reagent='DIC',
        additive='HOBt (anhydrous)',base='',solvent='DMF',preset='Custom',
        synthesis_form=kind,branch_point='K2',branch_arm='RG',branch_pg='Dde',
        branch_coupling_system='HBTU_NMM',branch_primary_eq='3',branch_secondary_eq='6',
        branch_coupling_solvent='DMF',selective_cleavage_system='TFA_DCM_1_5',
        selective_total_volume_ml='80',cyclic_coupling_system='HBTU_NMM',
        cyclic_product='head_to_tail_protected',cyclic_groups='catalog')
    gui=SPPSGui();gui.withdraw()
    try:
        gui.pm_add_peptide(build_item_payload(SimpleNamespace(),values))
        assert gui.pm_generate_selected() is True
        tree=gui.pm_selected_plan_tree
        cols=tree['columns']
        rows=[dict(zip(cols,tree.item(row,'values'))) for row in tree.get_children()]
        if kind=='branched':
            arm=[r for r in rows if 'BRANCH ARM' in str(r.get('Note')) and r.get('Reagent 1')]
            assert arm and all(r['Reagent 1']=='HBTU' and r['Base']=='NMM' for r in arm)
            assert all(float(r['R1 eq'])==3 and float(r['Base eq'])==6 for r in arm)
        else:
            assert any('Head-to-tail cyclization' in r['Unit name'] for r in rows)
            assert any('Selective cleavage' in r['Unit name'] for r in rows)
        if hasattr(gui, 'project_outdir'): gui.project_outdir.set(str(tmp_path/'output'))
        elif hasattr(gui, 'outdir'): gui.outdir.set(str(tmp_path/'output'))
        exported=gui.export_outputs()
        assert exported is not None
        method=pd.read_excel(exported,sheet_name='10_METHOD_REVIEWS')
        assert ('1.5% TFA / DCM' in method['system'].values) is (kind=='cyclic')
        assert '95% TFA / 2.5% TIS / 2.5% H2O' in method['system'].values
        assert 'HBTU / NMM' in method['system'].values
        if kind=='cyclic':
            mats=pd.read_excel(exported,sheet_name='02_SELECTED_MATERIALS_STEP')
            names=set(mats['material'].dropna().astype(str))
            assert not any('REVIEW' in name for name in names)
    finally:
        gui.destroy()


def test_global_cleavage_formula_and_site_labels_fail_closed():
    from spps_planner.reaction_planner_v9 import prepare_global_cleavage_review
    from suite_gui.modules.add_peptide_dialog import _sequence_site_labels, _site_position
    x=prepare_global_cleavage_review(scale_mmol=0.2,tfa_equivalents='100')
    assert x['tfa_volume_ml']==pytest.approx(0.2*100*114.02/1000/1.49,abs=0.00001)
    assert x['total_volume_ml']==pytest.approx(x['tfa_volume_ml']/0.95,abs=1e-5)
    assert _sequence_site_labels('SVS')==['1S','2V','3S']
    assert _sequence_site_labels('SCCS')==['1S','2C','3C','4S']
    assert _site_position('1S','SVS')==1
    assert _site_position('3S','SVS')==3
    with pytest.raises(ValueError,match='match'):
        _site_position('3C','SVS')
    with pytest.raises(ReactionPlanError):
        prepare_global_cleavage_review(scale_mmol=0.2,total_volume_ml=10,tfa_equivalents='100')


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='GUI display required')
@pytest.mark.parametrize('mode', ['branched','head_to_tail','disulfide'])
def test_canonical_route_plan_materials_cleavage_export(tmp_path,monkeypatch,mode):
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from suite_gui.modules import plan_workflow
    import pandas as pd
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    errors=[]
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:errors.append(a))
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    kwargs=dict(project='QA',peptide='Audit',sequence='AKG' if mode=='branched' else ('SVS' if mode=='head_to_tail' else 'SCCS'),
                scale='0.2',copies='1',resin='2-CTC',loading='0.8',apply_loading_calc='1',
                reagent='DIC',additive='HOBt (anhydrous)',base='',solvent='DMF',preset='Custom',
                synthesis_form='branched' if mode=='branched' else 'cyclic',
                branch_point='K2',branch_arm='RG',branch_pg='Dde',
                branch_coupling_system='HBTU_NMM',branch_primary_eq='3',branch_secondary_eq='6',
                branch_boc2o_eq='3',branch_boc_base_eq='3',branch_coupling_solvent='DMF',
                selective_cleavage_system='TFA_DCM_1_5',selective_total_volume_ml='80',
                cyclic_coupling_system='HBTU_NMM',cyclic_product='disulfide' if mode=='disulfide' else 'head_to_tail_deprotected',
                cyclic_groups='catalog',disulfide_site_a='2C',disulfide_site_b='3C',
                global_tfa_equivalents='100')
    gui=SPPSGui();gui.withdraw()
    try:
        item=build_item_payload(SimpleNamespace(),kwargs)
        assert ('selective_cleavage_review' in item)==(mode=='head_to_tail')
        gui.pm_add_peptide(item)
        assert gui.pm_generate_selected() is True, errors
        plan=pd.DataFrame([dict(zip(gui.pm_selected_plan_tree['columns'],gui.pm_selected_plan_tree.item(i,'values')))
                           for i in gui.pm_selected_plan_tree.get_children()])
        units=plan['Unit name'].to_list()
        if mode=='branched':
            assert units.index('N-terminal Boc protection — REVIEW')<next(i for i,u in enumerate(units) if u.startswith('Branch PG removal'))
            assert all('Selective cleavage' not in u for u in units)
        elif mode=='head_to_tail':
            assert units.index('Selective cleavage — REVIEW')<units.index('Head-to-tail cyclization — REVIEW')<units.index('Final global cleavage / deprotection — REVIEW')
        else:
            assert units.index('Global cleavage / thiol deprotection — REVIEW')<units.index('Disulfide Cys-Cys cyclization — REVIEW')
            assert not any('Selective cleavage' in u for u in units)
        assert gui.pm_apply_selected() is True if hasattr(gui,'pm_apply_selected') else gui.apply_change() is True
        path=tmp_path/'output';gui.outdir.set(str(path))
        exported=gui.export_outputs()
        assert exported
        materials=pd.read_excel(exported,sheet_name='02_SELECTED_MATERIALS_STEP')
        names=set(materials['material'].dropna().astype(str))
        assert not {'AcOH','TFE'} & names
        assert {'TFA','TIS','Water'} <= names
        if mode=='branched':
            assert 'Boc2O' in names
            assert float(materials.loc[materials.material=='Boc2O','planned_g'].dropna().iloc[0])>0
        if mode=='head_to_tail':
            assert float(materials.loc[(materials.material=='TFA')&(materials.step=='selective-cleavage'),'planned_mL'].iloc[0])==pytest.approx(1.2)
        methods=pd.read_excel(exported,sheet_name='10_METHOD_REVIEWS')
        assert ('selective_cleavage' in methods['stage'].values)==(mode=='head_to_tail')
        assert 'global_cleavage' in methods['stage'].values
        # For nonlinear topology only the selected actual Plan may be exported;
        # a linear-core-only workbook would contradict the routed chemistry.
        assert not (path/'spps_plan_core_engine.xlsx').exists()
        assert not (path/'core_engine_outputs').exists()
        import json
        saved=json.loads((path/'project_manager_state_v9.0.0.json').read_text(encoding='utf-8'))
        active=saved['pm_items'][saved['active_index']]
        assert active['synthesis_form']==('branched' if mode=='branched' else 'cyclic')
        assert active['global_cleavage_review']['system_id']=='TFA_TIS_WATER_95'
        if mode=='branched':
            assert active['branch_boc_review']['reagents'][0]['equivalents']==3
        if mode=='disulfide':
            assert active['v9_mass_options']['disulfide_sites']==[2,3]
        assert not errors
    finally:
        gui.destroy()

@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='GUI display required')
def test_edit_save_generates_current_plan_not_empty(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload, open_dialog
    from suite_gui.modules import plan_workflow
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    errors=[]
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:errors.append(a))
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    gui=SPPSGui();gui.withdraw()
    try:
        item=build_item_payload(SimpleNamespace(),dict(project='P',peptide='A',sequence='SVS',scale='0.2',copies='1',
            resin='2-CTC',loading='0.8',reagent='DIC',additive='HOBt (anhydrous)',base='',solvent='DMF',
            preset='Custom',synthesis_form='cyclic',cyclic_product='head_to_tail_protected'))
        gui.pm_add_peptide(item)
        assert gui.pm_generate_selected() is True
        original_len=len(gui.pm_selected_plan_tree.get_children())
        assert original_len>0
        active=gui.pm_current_index()
        win=open_dialog(gui,item_index=active)
        gui.add_peptide_dialog_vars['sequence'].set('SVSS')
        gui.update_idletasks()
        gui.add_peptide_confirm_button.invoke()
        gui.update_idletasks()
        assert gui.pm_items[active]['sequence']=='SVSS'
        assert gui.pm_items[active]['status']=='Calculated'
        assert len(gui.pm_selected_plan_tree.get_children())>0
        assert gui.apply_change() is True
        assert not errors
        assert not win.winfo_exists()
    finally:
        gui.destroy()


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='GUI display required')
def test_setup_cyclic_site_labels_saved_and_regenerated(tmp_path,monkeypatch):
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from suite_gui.modules import plan_workflow
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:None)
    gui=SPPSGui();gui.withdraw()
    try:
        item=build_item_payload(SimpleNamespace(),dict(project='P',peptide='A',sequence='SCCS',scale='0.2',copies='1',
            resin='2-CTC',loading='0.8',reagent='DIC',additive='HOBt (anhydrous)',base='',solvent='DMF',
            preset='Custom',synthesis_form='cyclic',cyclic_product='head_to_tail_deprotected'))
        gui.pm_add_peptide(item)
        gui.pm_refresh_cyclic_settings()
        assert '2C' in gui.pm_site_a_box['values']
        gui.pm_cyclic_product.set('disulfide')
        gui.pm_disulfide_site_a.set('2C')
        gui.pm_disulfide_site_b.set('3C')
        assert gui.pm_save_cyclic_selection() is True
        assert gui.pm_items[gui.pm_current_index()]['v9_mass_options']['disulfide_sites']==[2,3]
        units=[gui.pm_selected_plan_tree.item(i,'values')[1] for i in gui.pm_selected_plan_tree.get_children()]
        assert any('Disulfide' in u for u in units)
        assert not any('Selective cleavage' in u for u in units)
    finally:
        gui.destroy()

@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'), reason='Requires GUI display')
def test_operator_head_to_tail_review_reaches_plan_materials_excel_and_invalidates_on_copy_edit(tmp_path, monkeypatch):
    """Stored operator equivalents must not be stranded in method JSON only."""
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload, _replace_project_item
    from suite_gui.modules import plan_workflow
    from spps_planner.reaction_planner_v9 import prepare_reaction_review
    import pandas as pd
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA', str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'session.json',raising=False)
    errors=[]
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:errors.append(a))
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    values=dict(project='QA',peptide='Headtail',sequence='SVS',scale='0.2',copies='2',
                resin='2-CTC',loading='0.8',reagent='DIC',additive='HOBt (anhydrous)',
                base='',solvent='DMF',preset='Custom',synthesis_form='cyclic',
                cyclic_product='head_to_tail_protected',cyclic_groups='catalog')
    item=build_item_payload(SimpleNamespace(),values)
    method=prepare_reaction_review('SVS','2-CTC',scale_mmol=.2,copies=2,
        method_id='HBTU_NMM',equivalents={'HBTU':3,'NMM':6},
        concentration_mm=2,solvent='DMF',reaction_time_h=2)
    item['v9_mass_options']['reaction_review']=method
    gui=SPPSGui();gui.withdraw()
    try:
        gui.pm_add_peptide(item)
        assert gui.pm_generate_selected() is True, errors
        assert gui.apply_change() is True
        rows=[dict(zip(gui.pm_selected_plan_tree['columns'],
                gui.pm_selected_plan_tree.item(iid,'values')))
                for iid in gui.pm_selected_plan_tree.get_children()]
        ht=next(r for r in rows if r['Unit name'].startswith('Head-to-tail cyclization'))
        assert ht['Reagent 1']=='HBTU'
        assert float(ht['R1 eq'])==3
        assert float(ht['R1 mmol'])==pytest.approx(.6)
        assert ht['Base']=='NMM'
        assert float(ht['Base mmol'])==pytest.approx(1.2)
        assert float(ht['Solvent mL'])==pytest.approx(100)
        assert ht['R1 amount']=='' and ht['Base amount']==''
        gui.outdir.set(str(tmp_path/'output'))
        xlsx=gui.export_outputs()
        assert xlsx is not None, errors
        exported=pd.read_excel(xlsx,sheet_name='02_SELECTED_MATERIALS_STEP')
        cycl=exported[exported.step=='cyclization']
        assert float(cycl.loc[cycl.material=='HBTU','planned_mmol'].iloc[0])==pytest.approx(.6)
        assert float(cycl.loc[cycl.material=='NMM','planned_mmol'].iloc[0])==pytest.approx(1.2)
        assert float(cycl.loc[cycl.material=='DMF','planned_mL'].iloc[0])==pytest.approx(100)
        assert cycl.loc[cycl.material=='HBTU','planned_g'].isna().all()
        assert not errors
        changed=build_item_payload(SimpleNamespace(), {**values,'copies':'3'})
        updated=_replace_project_item(gui,gui.pm_current_index(),changed)
        assert updated['v9_mass_options']['reaction_review'] is None
    finally:
        gui.destroy()


def test_unreviewed_stale_headtail_method_never_shows_old_equivalents():
    """A stale review is not allowed to populate a changed peptide's materials."""
    from types import SimpleNamespace
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from spps_planner.reaction_planner_v9 import prepare_reaction_review
    item=build_item_payload(SimpleNamespace(),dict(project='P',peptide='A',sequence='SVS',scale='0.2',
        copies='2',resin='2-CTC',loading='0.8',synthesis_form='cyclic',
        cyclic_product='head_to_tail_protected',cyclic_groups='catalog',
        reagent='DIC',additive='HOBt (anhydrous)',base='',solvent='DMF',preset='Custom'))
    item['v9_mass_options']['reaction_review']=prepare_reaction_review('SVS','2-CTC',
        scale_mmol=.2,copies=1,method_id='HBTU_NMM',equivalents={'HBTU':3,'NMM':6},
        concentration_mm=2,solvent='DMF',reaction_time_h=2)
    # Rather than requiring Tk, verify stale numeric fields through the
    # real stored-review validator used by Plan generation.
    from spps_planner.reaction_planner_v9 import validate_stored_reaction_review, ReactionPlanError
    with pytest.raises(ReactionPlanError, match='copies changed'):
        validate_stored_reaction_review(item['v9_mass_options']['reaction_review'],
            sequence='SVS',resin='2-CTC',scale_mmol=.2,copies=2,side_chain_mode='catalog')

@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'), reason='Requires GUI display')
def test_stale_headtail_review_is_visible_as_warning_but_not_counted(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from suite_gui.modules import plan_workflow
    from spps_planner.reaction_planner_v9 import prepare_reaction_review
    import pandas as pd
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:None)
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    item=build_item_payload(SimpleNamespace(),dict(project='P',peptide='A',sequence='SVS',scale='0.2',
        copies='3',resin='2-CTC',loading='0.8',synthesis_form='cyclic',
        cyclic_product='head_to_tail_protected',cyclic_groups='catalog',
        reagent='DIC',additive='HOBt (anhydrous)',base='',solvent='DMF',preset='Custom'))
    item['v9_mass_options']['reaction_review']=prepare_reaction_review('SVS','2-CTC',
        scale_mmol=.2,copies=2,method_id='HBTU_NMM',equivalents={'HBTU':3,'NMM':6},
        concentration_mm=2,solvent='DMF',reaction_time_h=2)
    gui=SPPSGui();gui.withdraw()
    try:
        gui.pm_add_peptide(item)
        assert gui.pm_generate_selected() is True
        rows=[dict(zip(gui.pm_selected_plan_tree['columns'],
            gui.pm_selected_plan_tree.item(iid,'values')))
            for iid in gui.pm_selected_plan_tree.get_children()]
        reviewed=next(r for r in rows if r['Unit name'].startswith('Head-to-tail cyclization'))
        assert 'RE-REVIEW REQUIRED' in reviewed['Note']
        assert reviewed['R1 mmol']=='' and reviewed['Base mmol']==''
        gui.outdir.set(str(tmp_path/'out'))
        xlsx=gui.export_outputs()
        materials=pd.read_excel(xlsx,sheet_name='02_SELECTED_MATERIALS_STEP')
        assert not ((materials['step']=='cyclization') & (materials['material']=='HBTU')).any()
        review=pd.read_excel(xlsx,sheet_name='09_CYCLIC_REVIEW')
        assert review.iloc[-1]['review_status']=='RE-REVIEW REQUIRED'
        assert pd.isna(review.iloc[-1]['reaction_review_json'])
        methods=pd.read_excel(xlsx,sheet_name='10_METHOD_REVIEWS')
        entry=methods[methods['stage']=='cyclization'].iloc[-1]
        assert entry['status']=='RE-REVIEW REQUIRED'
        assert 'mmol_total' not in entry['details_json']
        legacy=gui.cyclic_review_rows()
        assert legacy[-1]['reaction_review_status']=='re-review required'
        assert legacy[-1]['reaction_review_json']==''
        gui.pm_refresh_cyclic_settings()
        assert 're-review required' in gui.pm_cyclic_status.get()
    finally:
        gui.destroy()


def test_edc_hcl_nhs_registered_for_branch_and_head_to_tail():
    from spps_planner.reaction_planner_v9 import prepare_branch_coupling_review,validate_stored_reaction_review
    assert ('EDC_NHS','EDC·HCl / NHS') in method_choices()
    assert REACTION_METHODS['EDC_NHS']['reagents'] == [('EDC·HCl','coupling_reagent'),('NHS','additive')]
    branch=prepare_branch_coupling_review('EDC_NHS',equivalents={'EDC-HCl':'3','NHS':'3'},solvent='DMF')
    assert [r['name'] for r in branch['reagents']]==['EDC·HCl','NHS']
    assert [r['equivalents'] for r in branch['reagents']]==[3.0,3.0]
    review=prepare_reaction_review('SVS','2-CTC',scale_mmol=.1,copies=2,
        method_id='EDC_NHS',equivalents={'EDC-HCl':3,'NHS':2},
        concentration_mm=1.0,solvent='DMF',reaction_time_h='4')
    assert review['approval']=='DRAFT_NOT_APPROVED'
    assert review['reagents'][0]['mmol_total']==pytest.approx(.6)
    assert review['reagents'][1]['role']=='additive'
    assert any(flag['code']=='EDC_NHS_ACTIVE_ESTER_UNVALIDATED'
               for flag in review['literature_evidence']['risk_flags'])
    assert validate_stored_reaction_review(review,sequence='SVS',resin='2-CTC',
        scale_mmol=.1,copies=2)==review
    with pytest.raises(ReactionPlanError,match='Duplicate'):
        prepare_reaction_review('SVS','2-CTC',scale_mmol=.1,method_id='EDC_NHS',
            equivalents={'EDC·HCl':3,'EDC-HCl':3,'NHS':3})

def test_edc_nhs_add_peptide_preset_keeps_bottle_identity():
    from suite_gui.modules.add_peptide_dialog import PRESETS, build_item_payload
    from types import SimpleNamespace
    key='EDC-HCl + NHS'
    assert PRESETS[key][1:]==('EDC-HCl','NHS','','DMF')
    item=build_item_payload(SimpleNamespace(),dict(project='QA',peptide='EDC NHS',
        sequence='SVS',scale='.1',copies='1',resin='2-CTC',loading='.8',
        reagent='EDC-HCl',additive='NHS',base='',solvent='DMF',preset=key))
    assert item['default_reagent']=='EDC-HCl'
    assert item['default_catalyst']=='NHS'
    assert item['method_label']==key

@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'), reason='GUI display required')
def test_edc_nhs_full_route_plan_materials_and_export_match(tmp_path, monkeypatch):
    """One operator draft flows through the selected Plan and all output formats."""
    import pandas as pd
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from suite_gui.modules import plan_workflow

    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:None)
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    item=build_item_payload(SimpleNamespace(),dict(
        project='RouteQA',peptide='EDC-NHS',sequence='SVS',scale='0.2',copies='2',
        resin='2-CTC',loading='0.8',synthesis_form='cyclic',
        cyclic_product='head_to_tail_protected',cyclic_groups='catalog',
        cyclic_coupling_system='EDC_NHS',reagent='EDC-HCl',additive='NHS',
        base='',solvent='DMF',preset='EDC-HCl + NHS'))
    item['v9_mass_options']['reaction_review']=prepare_reaction_review(
        'SVS','2-CTC',scale_mmol=.2,copies=2,method_id='EDC_NHS',
        equivalents={'EDC-HCl':3,'NHS':2},solvent='DMF',concentration_mm=2,
        reaction_time_h=4,side_chain_mode='catalog')
    gui=SPPSGui();gui.withdraw()
    try:
        gui.pm_add_peptide(item)
        assert gui.pm_generate_selected() is True
        rows=[dict(zip(gui.pm_selected_plan_tree['columns'],gui.pm_selected_plan_tree.item(iid,'values')))
              for iid in gui.pm_selected_plan_tree.get_children()]
        step=next(row for row in rows if row['Unit name'].startswith('Head-to-tail cyclization'))
        assert step['Reagent 1']=='EDC·HCl'
        assert step['Reagent 2 / catalyst']=='NHS'
        assert float(step['R1 mmol'])==pytest.approx(.6)
        assert float(step['R2 mmol'])==pytest.approx(.4)
        gui.outdir.set(str(tmp_path/'out'))
        exported=gui.export_outputs()
        assert exported is not None
        xlsx=tmp_path/'out'/'project_manager_selected_outputs_v9.0.0.xlsx'
        assert xlsx.is_file()
        output=pd.read_excel(xlsx,sheet_name='01_SELECTED_PLAN_VISIBLE',keep_default_na=False)
        corresponding=output[output['Unit name'].str.startswith('Head-to-tail cyclization')].iloc[-1]
        assert corresponding['Reagent 1']==step['Reagent 1']
        assert corresponding['Reagent 2 / catalyst']==step['Reagent 2 / catalyst']
        assert float(corresponding['R1 mmol'])==pytest.approx(.6)
        from_csv=pd.read_csv(tmp_path/'out'/'01_SELECTED_PLAN_VISIBLE.csv',keep_default_na=False)
        csv_step=from_csv[from_csv['Unit name'].str.startswith('Head-to-tail cyclization')].iloc[-1]
        assert csv_step['Reagent 1']=='EDC·HCl'
        assert float(csv_step['R1 mmol'])==pytest.approx(float(corresponding['R1 mmol']))
        assert float(csv_step['R2 mmol'])==pytest.approx(float(corresponding['R2 mmol']))
        materials=pd.read_excel(xlsx,sheet_name='02_SELECTED_MATERIALS_STEP')
        assert 'EDC·HCl' in materials['material'].values
        assert 'NHS' in materials['material'].values
        review=pd.read_excel(xlsx,sheet_name='09_CYCLIC_REVIEW')
        assert review.iloc[-1]['structural_check']=='CROSSCHECK_PASS'
        assert review.iloc[-1]['linear_protected_neutral_mw_g_mol'] > review.iloc[-1]['cyclic_protected_neutral_mw_g_mol']
        ion=json.loads(review.iloc[-1]['theoretical_ions_json'])
        assert ion['status']=='THEORETICAL_ONLY_NOT_OBSERVED'
        assert ion['positive_ion_candidates'][0]['label']=='[M+H]+'
        assert review.iloc[-1]['product_exact_mass'] > 0
        methods=pd.read_excel(xlsx,sheet_name='10_METHOD_REVIEWS')
        assert 'EDC·HCl / NHS' in methods['system'].values
        from_json=json.loads((tmp_path/'out'/'project_manager_state_v9.0.0.json').read_text(encoding='utf-8'))
        assert any((it.get('v9_mass_options') or {}).get('reaction_review',{}).get('system_id')=='EDC_NHS' for it in from_json['pm_items'])
    finally:
        gui.destroy()

@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'), reason='GUI display required')
def test_edc_nhs_branch_uses_independent_system_in_plan_and_exports(tmp_path, monkeypatch):
    import pandas as pd
    from types import SimpleNamespace
    from suite_gui.classic_2094_tk_gui import SPPSGui
    from suite_gui.modules.add_peptide_dialog import build_item_payload
    from suite_gui.modules import plan_workflow
    monkeypatch.setenv('SPPS_PLANNER_USER_DATA',str(tmp_path/'profile'))
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'local'))
    monkeypatch.setattr(SPPSGui,'_state_file_path',lambda self:tmp_path/'state.json',raising=False)
    monkeypatch.setattr(plan_workflow.messagebox,'showerror',lambda *a,**kw:None)
    monkeypatch.setattr(plan_workflow.messagebox,'showinfo',lambda *a,**kw:None)
    item=build_item_payload(SimpleNamespace(),dict(
        project='QA',peptide='B-EDC',sequence='AKG',scale='.2',copies='1',
        resin='2-CTC',loading='.8',reagent='DIC',additive='HOBt (anhydrous)',
        base='',solvent='DMF',preset='Custom',synthesis_form='branched',
        branch_point='K2',branch_arm='RG',branch_pg='Dde',
        branch_coupling_system='EDC_NHS',branch_primary_eq='3',branch_secondary_eq='2',
        branch_coupling_solvent='DMF'))
    gui=SPPSGui();gui.withdraw()
    try:
        gui.pm_add_peptide(item)
        assert gui.pm_generate_selected() is True
        rows=[dict(zip(gui.pm_selected_plan_tree['columns'],gui.pm_selected_plan_tree.item(row,'values')))
              for row in gui.pm_selected_plan_tree.get_children()]
        branch=[r for r in rows if 'BRANCH ARM' in str(r.get('Note')) and r.get('Reagent 1')]
        assert branch
        assert all(r['Reagent 1']=='EDC·HCl' and r['Reagent 2 / catalyst']=='NHS' for r in branch)
        assert all(float(r['R1 eq'])==3 and float(r['R2 eq'])==2 for r in branch)
        assert all(not str(r.get('Unit name','')).startswith('Selective cleavage') for r in rows)
        gui.outdir.set(str(tmp_path/'out'))
        file=gui.export_outputs()
        assert file is not None
        methods=pd.read_excel(file,sheet_name='10_METHOD_REVIEWS')
        assert 'EDC·HCl / NHS' in methods['system'].values
        exported=pd.read_excel(file,sheet_name='01_SELECTED_PLAN_VISIBLE')
        assert 'EDC·HCl' in exported['Reagent 1'].values
        assert 'NHS' in exported['Reagent 2 / catalyst'].values
    finally:
        gui.destroy()
