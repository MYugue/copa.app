"""
pangare_sync_v2.py — Bolão Pangaré · Copa 2026 · Mata-Mata
"""

import os, sys, argparse, logging
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DATABASE_URL        = os.environ.get("DATABASE_URL", "")
FOOTBALL_DATA_TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
API_BASE = "https://api.football-data.org/v4"
HEADERS  = {"X-Auth-Token": FOOTBALL_DATA_TOKEN, "Accept": "application/json"}

PHASE_MAP = {
    "LAST_32":        "Oitavas de Final",
    "QUARTER_FINALS": "Quartas de Final",
    "SEMI_FINALS":    "Semifinal",
    "FINAL":          "Final",
}

TEAM_NAME_PT = {
    "Brazil":"Brasil","Argentina":"Argentina","France":"França","Germany":"Alemanha",
    "Spain":"Espanha","Portugal":"Portugal","England":"Inglaterra","Netherlands":"Holanda",
    "Belgium":"Bélgica","Uruguay":"Uruguai","Colombia":"Colômbia","Mexico":"México",
    "United States":"Estados Unidos","Canada":"Canadá","Morocco":"Marrocos","Senegal":"Senegal",
    "Japan":"Japão","South Korea":"Coréia do Sul","Australia":"Austrália","Switzerland":"Suíça",
    "Croatia":"Croácia","Norway":"Noruega","Austria":"Áustria","Algeria":"Argélia",
    "Iraq":"Iraque","Jordan":"Jordânia","Uzbekistan":"Uzbequistão","DR Congo":"RD do Congo",
    "Bosnia and Herzegovina":"Bósnia e Herzegovina","Sweden":"Suécia","Turkey":"Turquia",
    "Czech Republic":"República Tcheca","South Africa":"África do Sul","Paraguay":"Paraguai",
    "Haiti":"Haiti","Scotland":"Escócia","Ivory Coast":"Costa do Marfim","Curaçao":"Curaçao",
    "Egypt":"Egito","New Zealand":"Nova Zelândia","Cabo Verde":"Cabo Verde","Panama":"Panamá",
    "Ecuador":"Equador","Tunisia":"Tunísia","Ghana":"Gana","Saudi Arabia":"Arábia Saudita",
    "Iran":"Irã","Qatar":"Catar","Serbia":"Sérvia",
}

def calc_points(gh, ga, rh, ra):
    # 5 pts placar exato | 3 pts resultado certo | +1 por gol de cada time (se resultado certo)
    # erra resultado = 0 pts (sem bônus parcial)
    def w(h, a): return "HOME" if h > a else "AWAY" if h < a else "DRAW"
    if gh == rh and ga == ra: return 5, "exact"
    gw, rw = w(gh, ga), w(rh, ra)
    if gw != rw: return 0, "miss"
    bonus = (1 if gh == rh else 0) + (1 if ga == ra else 0)
    return 3 + bonus, "result+bonus" if bonus else "result"

def test_scoring():
    cases = [
        (3,1,3,1,5,"Placar exato"),
        (0,0,0,0,5,"Placar exato (0x0)"),
        (1,1,1,1,5,"Placar exato (empate)"),
        (3,1,1,0,3,"Resultado certo sem gol igual (3x1 vs 1x0)"),
        (3,1,3,0,4,"Resultado certo + gol de um time (home)"),
        (3,1,2,1,4,"Resultado certo + gol de um time (away)"),
        (3,1,4,2,3,"Resultado certo sem gol igual"),
        (1,1,0,0,3,"Empate vs empate (placar diferente)"),
        (2,0,0,1,0,"Errou vencedor"),
        (3,0,1,1,0,"Palpitou vitória, deu empate"),
        (2,1,1,2,0,"Errou resultado (números invertidos) → 0 pts"),
    ]
    print(f"\n{'Palpite':<10} {'Resultado':<12} {'Esperado':<10} {'Obtido':<10} {'Status':<8} Descrição")
    print("─" * 75)
    all_ok = True
    for gh, ga, rh, ra, expected, desc in cases:
        pts, cat = calc_points(gh, ga, rh, ra)
        ok = pts == expected
        if not ok: all_ok = False
        print(f"{gh}x{ga:<8} {rh}x{ra:<10} {expected:<10} {pts:<10} {'OK' if ok else 'ERRO':<8} {desc}")
    print("─" * 75)
    print("Todos os testes passaram!\n" if all_ok else "FALHAS ENCONTRADAS!\n")
    return all_ok

def fetch_knockout_matches():
    url = f"{API_BASE}/competitions/WC/matches"
    params = {"stage": ",".join(PHASE_MAP.keys())}
    log.info(f"Consultando {url}")
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    except requests.RequestException as e:
        log.error(f"Erro de rede: {e}"); return []
    if resp.status_code == 429: log.warning("Rate limit atingido."); return []
    if not resp.ok: log.error(f"Erro API {resp.status_code}: {resp.text[:200]}"); return []
    matches = resp.json().get("matches", [])
    log.info(f"{len(matches)} partidas recebidas.")
    return matches

def compute_real_score(m):
    """Retorna (home_goals, away_goals) usando regularTime+extraTime quando
    o jogo foi decidido na prorrogação ou pênaltis, senão usa fullTime."""
    score = m.get("score", {})
    duration = score.get("duration", "REGULAR")

    if duration in ("EXTRA_TIME", "PENALTY_SHOOTOUT"):
        rt = score.get("regularTime", {}) or {}
        et = score.get("extraTime", {}) or {}
        home_goals = (rt.get("home") or 0) + (et.get("home") or 0)
        away_goals = (rt.get("away") or 0) + (et.get("away") or 0)
    else:
        ft = score.get("fullTime", {}) or {}
        home_goals = ft.get("home")
        away_goals = ft.get("away")

    return home_goals, away_goals, duration


def parse_match(m):
    stage = m.get("stage", "")
    if stage not in PHASE_MAP: return None
    home_goals, away_goals, duration = compute_real_score(m)
    ht = m.get("homeTeam", {}).get("name")
    at = m.get("awayTeam", {}).get("name")
    return {
        "external_id": m["id"],
        "phase":       stage,
        "phase_label": PHASE_MAP[stage],
        "match_date":  m.get("utcDate"),
        "home_team":   TEAM_NAME_PT.get(ht, ht),
        "away_team":   TEAM_NAME_PT.get(at, at),
        "home_goals":  home_goals,
        "away_goals":  away_goals,
        "status":      m.get("status", "SCHEDULED"),
    }

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def upsert_match(cur, match, dry_run):
    if dry_run:
        log.info(f"[DRY-RUN] {match['phase_label']} · {match.get('home_team','TBD')} x {match.get('away_team','TBD')} · {match['status']}")
        return False, None
    cur.execute("""
        INSERT INTO knockout_matches
            (external_id, phase, phase_label, match_date, home_team, away_team, home_goals, away_goals, status, updated_at)
        VALUES
            (%(external_id)s, %(phase)s, %(phase_label)s, %(match_date)s, %(home_team)s, %(away_team)s, %(home_goals)s, %(away_goals)s, %(status)s, NOW())
        ON CONFLICT (external_id) DO UPDATE SET
            home_team=EXCLUDED.home_team, away_team=EXCLUDED.away_team,
            home_goals=EXCLUDED.home_goals, away_goals=EXCLUDED.away_goals,
            status=EXCLUDED.status, updated_at=NOW()
        RETURNING id, status
    """, match)
    row = cur.fetchone()
    if not row: return False, None
    just_finished = (row["status"] == "FINISHED" and match.get("home_goals") is not None)
    return just_finished, row["id"]

def recalc_match(cur, db_id, dry_run):
    if dry_run: log.info(f"[DRY-RUN] Calcularia pontos para match_id={db_id}"); return
    cur.execute("SELECT calculate_knockout_points(%s)", (db_id,))
    log.info(f"Pontos recalculados para match_id={db_id}")

def print_ranking(cur):
    cur.execute("SELECT posicao, name, grupos_pts, mm_pts, total_pts FROM ranking_geral ORDER BY posicao")
    rows = cur.fetchall()
    log.info("─" * 52)
    log.info(f"{'#':<4} {'Nome':<20} {'Grupos':>7} {'M-M':>6} {'Total':>7}")
    log.info("─" * 52)
    for r in rows:
        log.info(f"{r['posicao']:<4} {r['name']:<20} {r['grupos_pts']:>7} {r['mm_pts']:>6} {r['total_pts']:>7}")
    log.info("─" * 52)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force",        action="store_true")
    parser.add_argument("--dry-run",      action="store_true")
    parser.add_argument("--test-scoring", action="store_true")
    args = parser.parse_args()

    if args.test_scoring:
        sys.exit(0 if test_scoring() else 1)

    if not DATABASE_URL:
        log.error("DATABASE_URL não definida."); sys.exit(1)

    raw = fetch_knockout_matches()
    if not raw:
        log.warning("Nenhuma partida da API. Encerrando."); sys.exit(0)

    parsed = [m for m in (parse_match(r) for r in raw) if m]
    log.info(f"{len(parsed)} partidas de mata-mata para processar.")

    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                newly_finished = []
                for match in parsed:
                    finished, db_id = upsert_match(cur, match, args.dry_run)
                    if finished and db_id:
                        newly_finished.append(db_id)
                if newly_finished:
                    log.info(f"{len(newly_finished)} jogos encerrados → calculando pontos...")
                    for db_id in newly_finished:
                        recalc_match(cur, db_id, args.dry_run)
                if args.force and not args.dry_run:
                    cur.execute("SELECT id FROM knockout_matches WHERE status='FINISHED' AND home_goals IS NOT NULL")
                    for r in cur.fetchall():
                        recalc_match(cur, r["id"], args.dry_run)
                if not args.dry_run:
                    print_ranking(cur)
        log.info("Sync concluído.")
    except Exception as e:
        log.error(f"Erro: {e}"); raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
