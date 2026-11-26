"""Reviewed literature provenance for SPPS Planner V9.0.0 reaction drafts.

Only literature-backed *cautions and context* are returned. No paper is
represented as validating the current sequence, its input ratios or yield.
This module intentionally uses stdlib-only static records to remain available
in packaged/PyInstaller builds without needing a separate bundled JSON file.
"""
from __future__ import annotations

import copy

# Manually curated 2026-11-08 from the linked primary abstracts/full text.
# stable reference IDs allow the human-readable catalog and saved drafts to
# carry usable citations. Bibliographic facts, not copied article text.
REACTION_REFERENCES = {
    'YAN_2015_EDC_NHS_MECHANISM': {
        'title': 'EDC/NHS activation mechanism of polymethacrylic acid: anhydride versus NHS-ester',
        'authors': 'Yan et al.', 'year': 2015,
        'doi': '10.1039/C5RA13844B',
        'url': 'https://pubs.rsc.org/en/content/articlehtml/2015/ra/c5ra13844b',
        'scope': 'Mechanistic study on polymer carboxyl groups and side pathways; NOT experimental validation of peptide head-to-tail cyclization.',
    },
    'BARLOS_1991_CTC': {
        'title': '2-Chlorotrityl chloride resin. Studies on anchoring of Fmoc-amino acids and peptide cleavage',
        'authors': 'Barlos et al.', 'year': 1991, 'pmid': '1917309',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/1917309/',
        'scope': 'Specific 2-CTC loading and mild cleavage of protected fragments; not a guarantee for every protecting group.',
    },
    'MCMURRAY_1994_CYCLIZATION': {
        'title': 'Influence of solid support, solvent and coupling reagent on the head-to-tail cyclization of resin-bound peptides',
        'authors': 'McMurray et al.', 'year': 1994, 'pmid': '7696839',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/7696839/',
        'scope': 'On-resin comparison; documents oligomerization and racemization concerns, not direct proof for solution protocols.',
    },
    'MALESEVIC_2004_DILUTION': {
        'title': 'An improved method for the solution cyclization of peptides under pseudo-high dilution conditions',
        'authors': 'Malesevic et al.', 'year': 2004, 'pmid': '15288942',
        'doi': '10.1016/j.jbiotec.2004.03.015',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/15288942/',
        'scope': 'Solution cyclization and intermolecular side products; concentration alone does not predict yield.',
    },
    'CONNORS_2022_PROTECTED_CYCLIZATION': {
        'title': 'Head-to-tail cyclization of side chain-protected linear peptides to recapitulate genetically-encoded cyclized peptides',
        'authors': 'Bouayad-Gervais et al.', 'year': 2022, 'pmid': '35864841',
        'doi': '10.1002/pep2.24254',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/35864841/',
        'scope': 'Evidence for side-chain-protected linear precursor strategy, not for arbitrary reagent ratios or sequences.',
    },
    'CHENEVAL_2014_CYCLIC_DISULFIDE': {
        'title': 'Fmoc-based synthesis of disulfide-rich cyclic peptides',
        'authors': 'Cheneval et al.', 'year': 2014,
        'pmid': '24918986', 'doi': '10.1021/jo500699m',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/24918986/',
        'scope': '2-CTC, protected peptide solution cyclization, then side-chain deprotection and disulfide oxidation on specific targets.',
    },
    'ERNY_2020_DIC_OXYMA_HCN': {
        'title': 'Minimizing HCN in DIC/Oxyma-Mediated Amide Bond-Forming Reactions',
        'authors': 'Erny et al.', 'year': 2020,
        'doi': '10.1021/acs.oprd.0c00227',
        'url': 'https://doi.org/10.1021/acs.oprd.0c00227',
        'scope': 'Reported HCN in DIC/Oxyma reactions in DMF; mitigation studies do not establish generic safe use.',
    },
    'MANNE_2021_CARBODIIMIDES': {
        'title': 'Amide Formation: Choosing the Safer Carbodiimide in Combination with OxymaPure to Avoid HCN Release',
        'authors': 'Manne et al.', 'year': 2021, 'pmid': '34424718',
        'doi': '10.1021/acs.orglett.1c02466',
        'url': 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11487715/',
        'scope': 'Comparative reagent study; DIC/Oxyma has HCN side-reaction, individual alternatives require their own assessment.',
    },
    'KONG_2025_ASPARTIMIDE': {
        'title': 'Aspartimide Formation and Its Prevention in Fmoc Chemistry Solid Phase Peptide Synthesis',
        'authors': 'Kong, van den Braak and Neumann', 'year': 2025,
        'pmid': '40857621', 'doi': '10.1002/cbic.202500490',
        'url': 'https://pubmed.ncbi.nlm.nih.gov/40857621/',
        'scope': 'Review of Asp-related base-mediated side reactions; no calibrated failure probability for a specific sequence.',
    },
}

# Evidence class intentionally remains 'reaction_class_context', not an
# experimentally verified recipe for the operator's sequence and conditions.
BASE_CYCLIZATION_REFERENCES = (
    'CONNORS_2022_PROTECTED_CYCLIZATION',
    'MALESEVIC_2004_DILUTION',
    'MCMURRAY_1994_CYCLIZATION',
)


def _add_flag(flags, code, severity, message, sources):
    flags.append({'code':code, 'severity':severity, 'message':message,
                  'reference_ids':list(sources), 'status':'LITERATURE_CONTEXT_ONLY'})


def review_reaction_evidence(*, method_id, solvent, resin, mass_states):
    """Return JSON-safe context-specific flags + literature references.

    Fail closed on invalid method instead of letting unsupported chemistry
    inherit unrelated papers. Does not authorize a procedure.
    """
    from .parser import parse_sequence
    valid={'DIC_HOBT','EDC_HOBT','HATU_DIEA','PYBOP_NMM','DIC_OXYMA','HBTU_NMM','HBTU_DIEA','EDC_NHS'}
    if method_id not in valid:
        raise ValueError('No literature assessment available for the selected reaction system.')
    flags=[]
    refs=list(BASE_CYCLIZATION_REFERENCES)
    if method_id == 'EDC_NHS':
        refs.append('YAN_2015_EDC_NHS_MECHANISM')
        _add_flag(flags, 'EDC_NHS_ACTIVE_ESTER_UNVALIDATED', 'caution',
                  'EDC/NHS is an NHS-active-ester coupling system, not a validated peptide macrocyclization protocol. Hydrolysis, N-acylurea formation, and intermolecular crosslinking compete with intended ring closure; no reagent ratios or yield are prescribed.',
                  ['YAN_2015_EDC_NHS_MECHANISM'])
    if method_id in ('HBTU_NMM','HBTU_DIEA'):
        _add_flag(flags, 'HBTU_SYSTEM_UNVALIDATED', 'caution',
                  'HBTU/base selection is an operator draft. No system-specific literature validation or optimized conditions are attached.', [])
    _add_flag(flags, 'CYCLIZATION_OLIGOMERIZATION', 'caution',
              'Intermolecular dimer/oligomer formation can compete with macrocyclization; review concentration, sequence, addition and analytical evidence.',
              ['MALESEVIC_2004_DILUTION','MCMURRAY_1994_CYCLIZATION'])
    _add_flag(flags, 'CYCLIZATION_EPIMERIZATION', 'caution',
              'Cyclization activation may cause epimerization; verify stereochemistry analytically where material.',
              ['MCMURRAY_1994_CYCLIZATION'])
    if 'CTC' in str(resin).upper() or 'CHLOROTRITYL' in str(resin).upper():
        refs.append('BARLOS_1991_CTC')
        _add_flag(flags, 'CTC_SELECTIVE_CLEAVAGE_REVIEW', 'caution',
                  'Mild 2-CTC cleavage may preserve selected side-chain protections; actual group retention and free termini must be checked experimentally.',
                  ['BARLOS_1991_CTC'])
    if method_id=='DIC_OXYMA':
        refs.extend(['ERNY_2020_DIC_OXYMA_HCN','MANNE_2021_CARBODIIMIDES'])
        in_dmf= 'DMF' in str(solvent).upper()
        _add_flag(flags, 'DIC_OXYMA_HCN', 'high',
                  ('DIC/Oxyma can generate toxic HCN in DMF; do not assume this formulation is hazard-free. Check current institutional SDS, engineering controls and approved SOP.' if in_dmf
                   else 'DIC/Oxyma can produce HCN under studied conditions including DMF; a different or unspecified solvent is NOT evidence of safety. Check SDS and approved SOP.'),
                  ['ERNY_2020_DIC_OXYMA_HCN','MANNE_2021_CARBODIIMIDES'])
    try:
        parsed=parse_sequence(str(mass_states['sequence']))
        has_asp=any(str(t).upper() in ('D','DD') or str(t).upper().startswith('D(')
                    for t in list(parsed.core_tokens)+list(parsed.branch_tokens))
    except (ValueError,TypeError,KeyError):
        has_asp=False
    try:
        has_cys=any(str(t).upper() in ('C','DC') or str(t).upper().startswith('C(')
                    for t in list(parsed.core_tokens)+list(parsed.branch_tokens))
    except (ValueError,TypeError,KeyError,UnboundLocalError):
        has_cys=False
    if has_cys and ('CTC' in str(resin).upper() or 'CHLOROTRITYL' in str(resin).upper()):
        refs.append('CHENEVAL_2014_CYCLIC_DISULFIDE')
        _add_flag(flags, 'CYS_ORTHOGONAL_OXIDATION_REVIEW', 'caution',
                  'Cys-containing macrocycles may require a separately controlled thiol deprotection/oxidation stage; this review does not plan disulfide bonds.',
                  ['CHENEVAL_2014_CYCLIC_DISULFIDE'])
    if has_asp:
        refs.append('KONG_2025_ASPARTIMIDE')
        _add_flag(flags, 'ASP_FMOC_DEPROTECTION', 'caution',
                  'Asp-containing sequence: Fmoc base-deprotection can promote aspartimide under some sequence/protection conditions; review actual conditions.',
                  ['KONG_2025_ASPARTIMIDE'])
    # Deduplicate while preserving stable order. Return records by value so
    # callers cannot mutate the global bibliography in another project.
    refs=list(dict.fromkeys(refs))
    return {
        'assessment':'LITERATURE_CONTEXT_NOT_VALIDATED_SOP',
        'references':[{**{'id':rid},**copy.deepcopy(REACTION_REFERENCES[rid])} for rid in refs],
        'risk_flags':flags,
    }
