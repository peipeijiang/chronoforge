"""Three-route input and evidence contracts. No network or paid calls."""
from pathlib import Path
from urllib.parse import urlparse
import json

MODES = {'recreation', 'product_video', 'hybrid'}
DEFAULTS = {
    'vision': 'codex-built-in', 'creative_author': 'codex-direct',
    'image': 'tt-image-2.5', 'image_fallback': 'tt-image-2',
    'video': 'omni_flash-10s', 'continuation': 'omni_flash-10s-fl',
    'variable_duration': 'omni-flash', 'text_overlay': 'postproduction',
}


def route(source=None, product_url=None):
    # Test the combined case FIRST; otherwise hybrid is unreachable.
    if product_url:
        u = urlparse(product_url)
        if u.scheme not in ('http', 'https') or not u.hostname:
            raise ValueError('product URL must be HTTP(S)')
    if source and urlparse(source).scheme in ('http', 'https'):
        raise ValueError('remote video link needs input clarification; provide a local uploaded video or --product-url')
    if source and product_url:
        return 'hybrid'
    if source:
        return 'recreation'
    if product_url:
        return 'product_video'
    raise ValueError('Please provide a product page link, an uploaded video, or both.')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def evidence_errors(root, mode):
    """Validate declared coverage, never infer observation from file existence."""
    root = Path(root)
    errors = []
    if mode not in MODES:
        return ['unknown route']
    if mode in ('recreation', 'hybrid'):
        try:
            source = read(root / 'analysis/source-evidence.json')
            if source.get('coverage', {}).get('full_duration_reviewed') is not True or not source.get('observations'):
                errors.append('full-duration source observations are required')
            if not source.get('audio_review'):
                errors.append('record audio review or an explicit unavailable limitation')
        except (OSError, ValueError):
            errors.append('source evidence is missing or invalid')
    if mode in ('product_video', 'hybrid'):
        try:
            # Product files are copied into the run, never edited in the external skill.
            manifest = read(root / 'evidence/product/product_manifest.json')
            analysis = read(root / 'evidence/product/image_analysis.json')
            brief = read(root / 'evidence/product/product_brief.json')
            a = [x.get('local_path') for x in manifest.get('images', [])]
            b = [x.get('local_path') for x in analysis.get('images', [])]
            if manifest.get('extraction_audit', {}).get('complete') is not True:
                errors.append('product extraction is incomplete')
            if not a or any(not x for x in a + b) or len(set(a)) != len(a) or sorted(a) != sorted(b):
                errors.append('product manifest and visual analysis must cover the same complete image set')
            for item in analysis.get('images', []):
                if item.get('analysis', {}).get('error'):
                    errors.append('failed product image analysis')
            for name in a:
                p = (root / 'evidence/product' / str(name)).resolve()
                if not p.is_relative_to((root / 'evidence/product').resolve()) or not p.is_file():
                    errors.append('product image must exist inside the portable product evidence directory')
            for key in ('confirmed_identity', 'confirmed_selling_points', 'confirmed_use_cases', 'misuse_risks_to_avoid'):
                if not brief.get(key):
                    errors.append('product brief missing ' + key)
            contract = brief.get('state_change_contract', {})
            if type(contract.get('required')) is not bool:
                errors.append('product brief needs explicit state-change applicability')
            if contract.get('required'):
                if not contract.get('states') or not contract.get('transitions'):
                    errors.append('state-changing product needs evidenced states/transitions')
                for transition in contract.get('transitions', []):
                    if not transition.get('evidence') or transition.get('render_policy') not in ('continuous_allowed', 'hard_cut_only', 'omit_transition'):
                        errors.append('state transition needs evidence and valid render policy')
                    if transition.get('evidence_level') == 'state_pair_only' and transition.get('render_policy') == 'continuous_allowed':
                        errors.append('endpoint-only evidence cannot authorize continuous motion')
            risk = brief.get('video_feasibility_plan', {})
            if type(risk.get('protect_product_configuration')) is not bool:
                errors.append('product brief needs an explicit configuration risk decision')
            claims = read(root / 'analysis/claim-ledger.json').get('claims', [])
            ids = [x.get('id') for x in claims]
            if not claims or any(not x for x in ids) or len(set(ids)) != len(ids):
                errors.append('unique claim ledger entries required')
            for claim in claims:
                if claim.get('status') not in ('supported', 'seller_claim', 'unresolved', 'rejected') or not claim.get('evidence'):
                    errors.append('claims need explicit status and source evidence')
        except (OSError, ValueError, TypeError):
            errors.append('product evidence/claim ledger is missing or invalid')
    return errors


def qa_focus(mode):
    return {
        'recreation': ['source fidelity', 'cause/action/reaction/payoff', 'approved adaptations'],
        'product_video': ['SKU and product structure', 'supported claims and proof', 'whole-ad story'],
        'hybrid': ['product truth priority', 'approved source-to-target adaptation', 'whole-ad story'],
    }[mode]


def required_qa(mode, kind):
    common = {
        'reference': {'identity', 'geometry', 'reference_roles'},
        'container': {'beat_coverage', 'state_continuity', 'audio', 'trim_completion'},
        'master': {'whole_story', 'seams', 'audio', 'text_readability'},
    }.get(kind, set())
    if mode in ('recreation', 'hybrid'):
        common = common | {'source_adaptation'}
    if mode in ('product_video', 'hybrid'):
        common = common | {'product_fidelity', 'claim_accuracy'}
    return common
