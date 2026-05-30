import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import pytz

# ══════════════════════════════════════════════
#  CONFIGURAÇÕES
# ══════════════════════════════════════════════
ADMIN_PASSWORD = "copa2026admin"
INVITE_CODE    = "copa2026"
DB_PATH        = "bolao.db"
DEADLINE       = datetime(2026, 6, 10, 23, 59, 0)
TZ_BR          = pytz.timezone("America/Sao_Paulo")

# ══════════════════════════════════════════════
#  BANDEIRAS — URLs do FlagCDN (confiável)
# ══════════════════════════════════════════════
FLAG_URLS = {
    "México":          "https://flagcdn.com/48x36/mx.png",
    "Coreia do Sul":   "https://flagcdn.com/48x36/kr.png",
    "Rep. Tcheca":     "https://flagcdn.com/48x36/cz.png",
    "África do Sul":   "https://flagcdn.com/48x36/za.png",
    "Canadá":          "https://flagcdn.com/48x36/ca.png",
    "Catar":           "https://flagcdn.com/48x36/qa.png",
    "Suíça":           "https://flagcdn.com/48x36/ch.png",
    "Bósnia e Herz.":  "https://flagcdn.com/48x36/ba.png",
    "Brasil":          "https://flagcdn.com/48x36/br.png",
    "Marrocos":        "https://flagcdn.com/48x36/ma.png",
    "Escócia":         "https://flagcdn.com/48x36/gb-sct.png",
    "Haiti":           "https://flagcdn.com/48x36/ht.png",
    "EUA":             "https://flagcdn.com/48x36/us.png",
    "Austrália":       "https://flagcdn.com/48x36/au.png",
    "Turquia":         "https://flagcdn.com/48x36/tr.png",
    "Paraguai":        "https://flagcdn.com/48x36/py.png",
    "Alemanha":        "https://flagcdn.com/48x36/de.png",
    "Costa do Marfim": "https://flagcdn.com/48x36/ci.png",
    "Equador":         "https://flagcdn.com/48x36/ec.png",
    "Curaçao":         "https://flagcdn.com/48x36/cw.png",
    "Holanda":         "https://flagcdn.com/48x36/nl.png",
    "Suécia":          "https://flagcdn.com/48x36/se.png",
    "Japão":           "https://flagcdn.com/48x36/jp.png",
    "Tunísia":         "https://flagcdn.com/48x36/tn.png",
    "Bélgica":         "https://flagcdn.com/48x36/be.png",
    "Irã":             "https://flagcdn.com/48x36/ir.png",
    "Nova Zelândia":   "https://flagcdn.com/48x36/nz.png",
    "Egito":           "https://flagcdn.com/48x36/eg.png",
    "Espanha":         "https://flagcdn.com/48x36/es.png",
    "Arábia Saudita":  "https://flagcdn.com/48x36/sa.png",
    "Uruguai":         "https://flagcdn.com/48x36/uy.png",
    "Cabo Verde":      "https://flagcdn.com/48x36/cv.png",
    "França":          "https://flagcdn.com/48x36/fr.png",
    "Iraque":          "https://flagcdn.com/48x36/iq.png",
    "Noruega":         "https://flagcdn.com/48x36/no.png",
    "Senegal":         "https://flagcdn.com/48x36/sn.png",
    "Argentina":       "https://flagcdn.com/48x36/ar.png",
    "Áustria":         "https://flagcdn.com/48x36/at.png",
    "Jordânia":        "https://flagcdn.com/48x36/jo.png",
    "Argélia":         "https://flagcdn.com/48x36/dz.png",
    "Portugal":        "https://flagcdn.com/48x36/pt.png",
    "Colômbia":        "https://flagcdn.com/48x36/co.png",
    "Uzbequistão":     "https://flagcdn.com/48x36/uz.png",
    "R.D. Congo":      "https://flagcdn.com/48x36/cd.png",
    "Inglaterra":      "https://flagcdn.com/48x36/gb-eng.png",
    "Gana":            "https://flagcdn.com/48x36/gh.png",
    "Panamá":          "https://flagcdn.com/48x36/pa.png",
    "Croácia":         "https://flagcdn.com/48x36/hr.png",
}

def flag_img(team, size=28):
    url = FLAG_URLS.get(team, "")
    if url:
        return f'<img src="{url}" style="height:{size}px; border-radius:3px; vertical-align:middle; margin:0 4px;">'
    return ""

# ══════════════════════════════════════════════
#  DADOS DOS JOGOS
# ══════════════════════════════════════════════
GROUPS = {
    "A": ["México", "Coreia do Sul", "Rep. Tcheca", "África do Sul"],
    "B": ["Canadá", "Catar", "Suíça", "Bósnia e Herz."],
    "C": ["Brasil", "Marrocos", "Escócia", "Haiti"],
    "D": ["EUA", "Austrália", "Turquia", "Paraguai"],
    "E": ["Alemanha", "Costa do Marfim", "Equador", "Curaçao"],
    "F": ["Holanda", "Suécia", "Japão", "Tunísia"],
    "G": ["Bélgica", "Irã", "Nova Zelândia", "Egito"],
    "H": ["Espanha", "Arábia Saudita", "Uruguai", "Cabo Verde"],
    "I": ["França", "Iraque", "Noruega", "Senegal"],
    "J": ["Argentina", "Áustria", "Jordânia", "Argélia"],
    "K": ["Portugal", "Colômbia", "Uzbequistão", "R.D. Congo"],
    "L": ["Inglaterra", "Gana", "Panamá", "Croácia"],
}

GROUP_COLORS = {
    "A": "#1a6b3a", "B": "#1a5ca8", "C": "#c8a000", "D": "#7b3fa0",
    "E": "#b33000", "F": "#0077a8", "G": "#3a7a00", "H": "#a04000",
    "I": "#1a5ca8", "J": "#7b3fa0", "K": "#1a6b3a", "L": "#a04000",
}

def get_all_matches():
    matches = []
    match_id = 1
    for g, teams in GROUPS.items():
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matches.append({"id": match_id, "group": g, "home": teams[i], "away": teams[j]})
                match_id += 1
    return matches

ALL_MATCHES = get_all_matches()
MATCH_BY_ID = {m["id"]: m for m in ALL_MATCHES}
GROUP_KEYS  = list(GROUPS.keys())

# ══════════════════════════════════════════════
#  BANCO DE DADOS
# ══════════════════════════════════════════════
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, nickname TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS guesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL, match_id INTEGER NOT NULL,
        home_goals INTEGER NOT NULL, away_goals INTEGER NOT NULL,
        submitted_at TEXT DEFAULT (datetime('now')),
        UNIQUE(nickname, match_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS results (
        match_id INTEGER PRIMARY KEY,
        home_goals INTEGER NOT NULL, away_goals INTEGER NOT NULL,
        updated_at TEXT DEFAULT (datetime('now')))""")
    conn.commit(); conn.close()

init_db()

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()
def is_deadline_passed():
    return datetime.now(TZ_BR).replace(tzinfo=None) > DEADLINE
def deadline_str():
    return DEADLINE.strftime("%d/%m/%Y às %H:%M") + " (Brasília)"

# ══════════════════════════════════════════════
#  BANCO — FUNÇÕES
# ══════════════════════════════════════════════
def register_user(name, nickname, password):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO participants (name, nickname, password) VALUES (?,?,?)",
                     (name.strip(), nickname.strip().lower(), hash_pw(password)))
        conn.commit(); conn.close(); return True, "Cadastro realizado!"
    except sqlite3.IntegrityError:
        conn.close(); return False, "Apelido já em uso. Escolha outro."

def login_user(nickname, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM participants WHERE nickname=? AND password=?",
                       (nickname.strip().lower(), hash_pw(password))).fetchone()
    conn.close(); return dict(row) if row else None

def save_guesses_batch(nickname, guesses_dict):
    conn = get_conn()
    for mid, (h, a) in guesses_dict.items():
        conn.execute("""INSERT INTO guesses (nickname,match_id,home_goals,away_goals) VALUES(?,?,?,?)
            ON CONFLICT(nickname,match_id) DO UPDATE SET
            home_goals=excluded.home_goals, away_goals=excluded.away_goals,
            submitted_at=datetime('now')""", (nickname, mid, h, a))
    conn.commit(); conn.close()

def get_guesses(nickname):
    conn = get_conn()
    rows = conn.execute("SELECT match_id,home_goals,away_goals FROM guesses WHERE nickname=?", (nickname,)).fetchall()
    conn.close(); return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in rows}

def get_all_guesses():
    conn = get_conn()
    rows = conn.execute("SELECT nickname,match_id,home_goals,away_goals FROM guesses").fetchall()
    conn.close(); return rows

def save_result(match_id, home, away):
    conn = get_conn()
    conn.execute("""INSERT INTO results (match_id,home_goals,away_goals) VALUES(?,?,?)
        ON CONFLICT(match_id) DO UPDATE SET
        home_goals=excluded.home_goals, away_goals=excluded.away_goals,
        updated_at=datetime('now')""", (match_id, home, away))
    conn.commit(); conn.close()

def get_results():
    conn = get_conn()
    rows = conn.execute("SELECT match_id,home_goals,away_goals FROM results").fetchall()
    conn.close(); return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in rows}

def get_all_participants():
    conn = get_conn()
    rows = conn.execute("SELECT name,nickname,created_at FROM participants ORDER BY name").fetchall()
    conn.close(); return [dict(r) for r in rows]

# ══════════════════════════════════════════════
#  PONTUAÇÃO
# ══════════════════════════════════════════════
def calc_result(h, a):
    return "H" if h > a else ("A" if h < a else "E")

def calc_points(gh, ga, rh, ra):
    pts, detail = 0, []
    if gh == rh and ga == ra:
        pts += 5; detail.append("✅ Placar exato (+5)")
    elif calc_result(gh, ga) == calc_result(rh, ra):
        pts += 3; detail.append("🏆 Resultado certo (+3)")
    if not (gh == rh and ga == ra):
        if gh == rh or ga == ra:
            pts += 1; detail.append("⚽ Gols de um time (+1)")
    return pts, detail

def calc_ranking():
    results = get_results(); guesses = get_all_guesses()
    scores, details = {}, {}
    for row in guesses:
        nick = row["nickname"]; mid = row["match_id"]
        if mid not in results: continue
        pts, det = calc_points(row["home_goals"], row["away_goals"], *results[mid])
        scores[nick] = scores.get(nick, 0) + pts
        details.setdefault(nick, []).append({"match_id": mid, "pts": pts, "detail": det})
    return scores, details

# ══════════════════════════════════════════════
#  CONFIG PÁGINA
# ══════════════════════════════════════════════
st.set_page_config(page_title="Bolão Copa 2026", page_icon="⚽", layout="wide")
st.markdown("""
<style>
.match-row {
    display: flex; align-items: center; justify-content: center;
    background: #f8f9fa; border-radius: 10px;
    padding: 10px 16px; margin-bottom: 8px;
    border: 1px solid #e0e0e0; gap: 8px;
}
.team-block {
    display: flex; align-items: center; gap: 8px;
    min-width: 180px;
}
.team-block.right { justify-content: flex-end; }
.team-name { font-size: 14px; font-weight: 600; color: #1a1a1a; }
.vs-sep { font-size: 13px; color: #bbb; margin: 0 6px; }
.group-badge {
    display: inline-block; padding: 5px 20px;
    border-radius: 20px; color: white;
    font-weight: 700; font-size: 15px; margin-bottom: 16px;
}
.pts-ok  { background:#1a6b3a; color:#fff; padding:2px 8px; border-radius:8px; font-size:11px; }
.pts-no  { background:#ddd;    color:#777; padding:2px 8px; border-radius:8px; font-size:11px; }
.real-info { text-align:center; font-size:12px; color:#777; margin-bottom:6px; }
.deadline-box { background:#fff3cd; border-left:4px solid #ffc107; padding:10px 14px; border-radius:4px; font-size:14px; margin-bottom:12px; }
.locked-box   { background:#f8d7da; border-left:4px solid #dc3545; padding:10px 14px; border-radius:4px; font-size:14px; margin-bottom:12px; }
div[data-testid="stNumberInput"] input {
    font-size:20px !important; font-weight:700 !important;
    text-align:center !important; color:#1a6b3a !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════
for k, v in [("user", None), ("admin_logged", False), ("auth_page", "login"), ("group_idx", 0)]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚽ Bolão Copa 2026")
    if st.session_state.user:
        st.success(f"👤 **{st.session_state.user['nickname']}**\n\n{st.session_state.user['name']}")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None; st.rerun()
    st.divider()
    if st.session_state.user or st.session_state.admin_logged:
        page = st.radio("Navegação", ["🏠 Início","📝 Meus Palpites","🏆 Ranking","📊 Resultados","🔐 Admin"])
    else:
        page = "🏠 Início"
    st.divider()
    st.markdown("**Pontuação:**\n- ✅ Placar exato → **5 pts**\n- 🏆 Resultado certo → **3 pts**\n- ⚽ Gols de 1 time → **+1 pt**")
    if is_deadline_passed():
        st.markdown(f'<div class="locked-box">🔒 <b>Encerrado</b><br>{deadline_str()}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="deadline-box">⏰ <b>Prazo:</b><br>{deadline_str()}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  INÍCIO
# ══════════════════════════════════════════════
if page == "🏠 Início":
    st.markdown("# ⚽ Bolão Copa do Mundo 2026")
    if st.session_state.user:
        u = st.session_state.user
        st.success(f"Bem-vindo de volta, **{u['name']}**! Use o menu lateral para fazer seus palpites.")
        scores, _ = calc_ranking()
        c1,c2,c3 = st.columns(3)
        c1.metric("👥 Participantes", len(get_all_participants()))
        c2.metric("⚽ Jogos com resultado", len(get_results()))
        c3.metric("📊 Seus pontos", scores.get(u["nickname"], 0))
    else:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown("### 🔑 Entrar")
            nick_l = st.text_input("Apelido", key="ln", placeholder="seu apelido")
            pw_l   = st.text_input("Senha",   key="lp", type="password")
            if st.button("Entrar", use_container_width=True, type="primary"):
                if nick_l and pw_l:
                    u = login_user(nick_l, pw_l)
                    if u: st.session_state.user = u; st.rerun()
                    else: st.error("Apelido ou senha incorretos.")
                else: st.warning("Preencha todos os campos.")
            if st.button("Criar conta", use_container_width=True):
                st.session_state.auth_page = "register"; st.rerun()
        with col2:
            st.markdown("### 📋 Criar conta")
            if st.session_state.auth_page == "register":
                inv  = st.text_input("Código de convite", key="ri", placeholder="enviado pelo organizador")
                nm   = st.text_input("Nome completo",     key="rn")
                nk   = st.text_input("Apelido",           key="rk", placeholder="aparece no ranking")
                pw   = st.text_input("Senha",             key="rp", type="password")
                pw2  = st.text_input("Confirmar senha",   key="rp2", type="password")
                if st.button("Cadastrar", use_container_width=True, type="primary"):
                    if not all([inv,nm,nk,pw,pw2]): st.error("Preencha todos os campos.")
                    elif inv.strip().lower() != INVITE_CODE.lower(): st.error("Código de convite inválido.")
                    elif pw != pw2: st.error("As senhas não coincidem.")
                    elif len(pw) < 4: st.error("Senha deve ter ao menos 4 caracteres.")
                    else:
                        ok, msg = register_user(nm, nk, pw)
                        if ok:
                            st.session_state.user = login_user(nk, pw)
                            st.session_state.auth_page = "login"; st.rerun()
                        else: st.error(msg)
                if st.button("Já tenho conta", use_container_width=True):
                    st.session_state.auth_page = "login"; st.rerun()
            else:
                st.info("Clique em **Criar conta** ao lado para se cadastrar.")

# ══════════════════════════════════════════════
#  MEUS PALPITES — grupo a grupo com bandeiras
# ══════════════════════════════════════════════
elif page == "📝 Meus Palpites":
    if not st.session_state.user: st.warning("Faça login primeiro."); st.stop()

    user   = st.session_state.user
    locked = is_deadline_passed()
    st.markdown("# 📝 Meus Palpites")

    if locked:
        st.markdown(f'<div class="locked-box">🔒 <b>Prazo encerrado.</b> Palpites bloqueados.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="deadline-box">⏰ Preencha os placares e salve grupo a grupo. Prazo: <b>{deadline_str()}</b></div>', unsafe_allow_html=True)

    my_guesses = get_guesses(user["nickname"])
    results    = get_results()

    # Progresso
    pct = int(len(my_guesses) / len(ALL_MATCHES) * 100)
    st.markdown(f"Progresso: **{len(my_guesses)}/{len(ALL_MATCHES)}** jogos preenchidos")
    st.progress(pct / 100)
    st.markdown("")

    # Grupo atual
    idx   = st.session_state.group_idx
    g     = GROUP_KEYS[idx]
    color = GROUP_COLORS[g]
    teams = GROUPS[g]
    matches_in_group = [m for m in ALL_MATCHES if m["group"] == g]

    # Badge do grupo
    teams_with_flags = " &nbsp;·&nbsp; ".join(
        f'{flag_img(t, 20)} {t}' for t in teams
    )
    st.markdown(
        f'<div class="group-badge" style="background:{color}">Grupo {g}</div>'
        f'<div style="font-size:13px;color:#555;margin-bottom:16px;">{teams_with_flags}</div>',
        unsafe_allow_html=True
    )

    group_inputs = {}
    for match in matches_in_group:
        mid      = match["id"]
        home     = match["home"]
        away     = match["away"]
        existing = my_guesses.get(mid, (0, 0))
        real     = results.get(mid)

        # Linha do jogo: [bandeira + nome] [input] × [input] [bandeira + nome]
        c1, c2, c3, c4, c5 = st.columns([4, 1.5, 0.4, 1.5, 4])
        with c1:
            st.markdown(
                f"<div style='text-align:right; padding-top:6px; font-size:14px; font-weight:600;'>"
                f"{home} &nbsp; {flag_img(home, 30)}</div>",
                unsafe_allow_html=True
            )
        with c2:
            h = st.number_input("", min_value=0, max_value=20,
                value=int(existing[0]), key=f"h_{mid}",
                label_visibility="collapsed", disabled=locked)
        with c3:
            st.markdown("<div style='text-align:center;padding-top:10px;font-size:18px;color:#bbb;'>×</div>",
                        unsafe_allow_html=True)
        with c4:
            a = st.number_input("", min_value=0, max_value=20,
                value=int(existing[1]), key=f"a_{mid}",
                label_visibility="collapsed", disabled=locked)
        with c5:
            st.markdown(
                f"<div style='padding-top:6px; font-size:14px; font-weight:600;'>"
                f"{flag_img(away, 30)} &nbsp; {away}</div>",
                unsafe_allow_html=True
            )

        # Resultado real
        if real:
            pts, det = calc_points(h, a, real[0], real[1])
            det_str  = " | ".join(det) if det else "0 pontos"
            badge    = f'<span class="pts-ok">{pts} pts</span>' if pts else '<span class="pts-no">0 pts</span>'
            st.markdown(
                f'<div class="real-info">Resultado real: <b>{real[0]}×{real[1]}</b> — {det_str} {badge}</div>',
                unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-bottom:6px'></div>", unsafe_allow_html=True)

        group_inputs[mid] = (h, a)

    if not locked:
        if st.button(f"💾 Salvar palpites do Grupo {g}", type="primary", use_container_width=True):
            save_guesses_batch(user["nickname"], group_inputs)
            st.success(f"✅ Palpites do Grupo {g} salvos com sucesso!")

    st.divider()

    # Navegação
    c_prev, c_info, c_next = st.columns([1, 2, 1])
    with c_prev:
        if idx > 0:
            if st.button("◀ Grupo anterior", use_container_width=True):
                st.session_state.group_idx -= 1; st.rerun()
    with c_info:
        st.markdown(
            f"<div style='text-align:center;padding-top:8px;color:#666;font-size:14px;'>"
            f"Grupo {idx+1} de {len(GROUP_KEYS)}</div>",
            unsafe_allow_html=True)
    with c_next:
        if idx < len(GROUP_KEYS) - 1:
            if st.button("Próximo grupo ▶", use_container_width=True):
                st.session_state.group_idx += 1; st.rerun()
        else:
            st.success("✅ Último grupo!")

# ══════════════════════════════════════════════
#  RANKING
# ══════════════════════════════════════════════
elif page == "🏆 Ranking":
    st.markdown("# 🏆 Ranking do Bolão")
    scores, _ = calc_ranking()
    participants = get_all_participants()
    if not participants: st.info("Nenhum participante ainda."); st.stop()

    nick_to_name  = {p["nickname"]: p["name"] for p in participants}
    all_scores    = {p["nickname"]: scores.get(p["nickname"], 0) for p in participants}
    sorted_scores = sorted(all_scores.items(), key=lambda x: -x[1])
    medals = ["🥇","🥈","🥉"]

    rows = [{"Pos": medals[i] if i<3 else f"{i+1}º",
             "Apelido": nick, "Nome": nick_to_name.get(nick,""),
             "Pontos": pts} for i,(nick,pts) in enumerate(sorted_scores)]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                 column_config={"Pos": st.column_config.TextColumn(width="small"),
                                "Pontos": st.column_config.NumberColumn(format="%d pts")})

    st.divider()
    st.markdown("### 🔍 Detalhes por participante")
    results  = get_results()
    options  = [f"{n} ({nick_to_name.get(n,'')})" for n,_ in sorted_scores]
    selected = st.selectbox("Escolha", options)
    if selected:
        sel_nick   = selected.split(" (")[0]
        my_guesses = get_guesses(sel_nick)
        detail_rows = []
        total = 0
        for mid,(rh,ra) in results.items():
            match = MATCH_BY_ID.get(mid)
            if not match: continue
            if mid in my_guesses:
                gh,ga = my_guesses[mid]
                pts,det = calc_points(gh,ga,rh,ra)
                total += pts
                detail_rows.append({"Grupo":f"Grupo {match['group']}",
                    "Jogo":f"{match['home']} × {match['away']}",
                    "Palpite":f"{gh}×{ga}","Real":f"{rh}×{ra}",
                    "Pontos":pts,"Detalhe":" | ".join(det) if det else "—"})
            else:
                detail_rows.append({"Grupo":f"Grupo {match['group']}",
                    "Jogo":f"{match['home']} × {match['away']}",
                    "Palpite":"—","Real":f"{rh}×{ra}","Pontos":0,"Detalhe":"Sem palpite"})
        if detail_rows:
            st.markdown(f"**Total: {total} pontos**")
            st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum resultado lançado ainda.")

# ══════════════════════════════════════════════
#  RESULTADOS
# ══════════════════════════════════════════════
# ══════════════════════════════════════════════
#  PÁGINA: RESULTADOS — meus palpites salvos
# ══════════════════════════════════════════════
elif page == "📊 Resultados":
    if not st.session_state.user:
        st.warning("Faça login para ver seus palpites.")
        st.stop()

    user = st.session_state.user
    st.markdown(f"# 📊 Meus Palpites Salvos")
    st.markdown(f"Confira abaixo tudo que você salvou, **{user['nickname']}**.")

    my_guesses = get_guesses(user["nickname"])
    results    = get_results()

    if not my_guesses:
        st.info("Você ainda não salvou nenhum palpite. Vá em 📝 Meus Palpites para preencher.")
        st.stop()

    for g, teams in GROUPS.items():
        matches_in_group = [m for m in ALL_MATCHES if m["group"] == g]
        color = GROUP_COLORS[g]

        # Verifica se tem algum palpite neste grupo
        group_guesses = [m for m in matches_in_group if m["id"] in my_guesses]
        if not group_guesses:
            continue

        st.markdown(
            f'<div style="background:{color};color:#fff;display:inline-block;'
            f'padding:4px 16px;border-radius:20px;font-weight:700;font-size:14px;'
            f'margin:14px 0 8px;">Grupo {g}</div>',
            unsafe_allow_html=True
        )

        for match in matches_in_group:
            mid  = match["id"]
            if mid not in my_guesses:
                continue

            gh, ga = my_guesses[mid]
            real   = results.get(mid)

            c1, c2, c3, c4, c5 = st.columns([3, 1, 0.3, 1, 3])
            with c1:
                st.markdown(
                    f"<div style='text-align:right;padding-top:6px;font-size:14px;font-weight:600;'>"
                    f"{match['home']} &nbsp; {flag_img(match['home'], 26)}</div>",
                    unsafe_allow_html=True)
            with c2:
                st.markdown(
                    f"<div style='text-align:center;padding-top:4px;"
                    f"font-size:22px;font-weight:700;color:#1a6b3a;'>{gh}</div>",
                    unsafe_allow_html=True)
            with c3:
                st.markdown(
                    "<div style='text-align:center;padding-top:8px;color:#aaa;'>×</div>",
                    unsafe_allow_html=True)
            with c4:
                st.markdown(
                    f"<div style='text-align:center;padding-top:4px;"
                    f"font-size:22px;font-weight:700;color:#1a6b3a;'>{ga}</div>",
                    unsafe_allow_html=True)
            with c5:
                st.markdown(
                    f"<div style='padding-top:6px;font-size:14px;font-weight:600;'>"
                    f"{flag_img(match['away'], 26)} &nbsp; {match['away']}</div>",
                    unsafe_allow_html=True)

            # Se resultado real já lançado, mostra pontuação
            if real:
                pts, det = calc_points(gh, ga, real[0], real[1])
                det_str  = " | ".join(det) if det else "0 pontos"
                badge    = f'<span style="background:#1a6b3a;color:#fff;padding:2px 8px;border-radius:8px;font-size:11px;">{pts} pts</span>' if pts else '<span style="background:#ddd;color:#777;padding:2px 8px;border-radius:8px;font-size:11px;">0 pts</span>'
                st.markdown(
                    f"<div style='text-align:center;font-size:12px;color:#777;margin-bottom:4px;'>"
                    f"Resultado real: <b>{real[0]}×{real[1]}</b> — {det_str} {badge}</div>",
                    unsafe_allow_html=True)

        st.markdown("<hr style='margin:8px 0;border:none;border-top:1px solid #eee;'>", unsafe_allow_html=True)

    # Resumo total
    st.divider()
    scores, _ = calc_ranking()
    total = scores.get(user["nickname"], 0)
    total_salvos = len(my_guesses)
    c1, c2 = st.columns(2)
    c1.metric("📝 Palpites salvos", f"{total_salvos} / {len(ALL_MATCHES)}")
    c2.metric("🏆 Pontos acumulados", total)

# ══════════════════════════════════════════════
#  ADMIN
# ══════════════════════════════════════════════
elif page == "🔐 Admin":
    st.markdown("# 🔐 Painel do Administrador")
    if not st.session_state.admin_logged:
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar como admin"):
            if pwd == ADMIN_PASSWORD: st.session_state.admin_logged = True; st.rerun()
            else: st.error("Senha incorreta!")
        st.stop()

    st.success("✅ Logado como administrador")
    if st.button("Sair do admin"): st.session_state.admin_logged = False; st.rerun()

    st.divider()
    st.markdown("### ⚙️ Configurações")
    c1,c2,c3 = st.columns(3)
    c1.info(f"**Código de convite:**\n\n`{INVITE_CODE}`")
    c2.info(f"**Prazo:**\n\n{deadline_str()}")
    c3.info(f"**Status:**\n\n{'🔒 Encerrado' if is_deadline_passed() else '🟢 Aberto'}")

    st.divider()
    st.markdown("### ⚽ Lançar Resultados")
    results   = get_results()
    group_sel = st.selectbox("Grupo", GROUP_KEYS, format_func=lambda g: f"Grupo {g}")
    for match in [m for m in ALL_MATCHES if m["group"] == group_sel]:
        mid = match["id"]; existing = results.get(mid, (0,0))
        c1,c2,c3,c4,c5,c6 = st.columns([4,1.5,0.4,1.5,4,1.2])
        with c1:
            st.markdown(f"<div style='text-align:right;padding-top:8px;font-size:13px;font-weight:600;'>"
                        f"{match['home']} {flag_img(match['home'],24)}</div>", unsafe_allow_html=True)
        with c2:
            rh = st.number_input("",min_value=0,max_value=20,value=int(existing[0]),key=f"rh_{mid}",label_visibility="collapsed")
        with c3:
            st.markdown("<div style='text-align:center;padding-top:10px;color:#bbb;'>×</div>", unsafe_allow_html=True)
        with c4:
            ra = st.number_input("",min_value=0,max_value=20,value=int(existing[1]),key=f"ra_{mid}",label_visibility="collapsed")
        with c5:
            st.markdown(f"<div style='padding-top:8px;font-size:13px;font-weight:600;'>"
                        f"{flag_img(match['away'],24)} {match['away']}</div>", unsafe_allow_html=True)
        with c6:
            if st.button("💾", key=f"sr_{mid}"):
                save_result(mid, rh, ra); st.success("Salvo!"); st.rerun()

    st.divider()
    st.markdown("### 👥 Participantes")
    participants = get_all_participants()
    if participants:
        st.dataframe(pd.DataFrame([{"Nome":p["name"],"Apelido":p["nickname"],
            "Cadastro":p["created_at"],"Palpites":len(get_guesses(p["nickname"]))}
            for p in participants]), hide_index=True, use_container_width=True)
    else: st.info("Nenhum participante ainda.")

    st.divider()
    with st.expander("🔑 Resetar senha de participante"):
        if participants:
            opt_reset = [f"{p['nickname']} — {p['name']}" for p in participants]
            sel_reset = st.selectbox("Selecione o participante", opt_reset, key="reset_sel")
            nova_senha  = st.text_input("Nova senha", key="nova_senha", type="password", placeholder="mínimo 4 caracteres")
            nova_senha2 = st.text_input("Confirmar nova senha", key="nova_senha2", type="password")
            if st.button("🔑 Resetar senha", type="primary", key="btn_reset"):
                if not nova_senha or not nova_senha2:
                    st.error("Preencha a nova senha.")
                elif nova_senha != nova_senha2:
                    st.error("As senhas não coincidem.")
                elif len(nova_senha) < 4:
                    st.error("Senha deve ter ao menos 4 caracteres.")
                else:
                    nick_reset = sel_reset.split(" — ")[0]
                    conn = get_conn()
                    conn.execute("UPDATE participants SET password=? WHERE nickname=?",
                                 (hash_pw(nova_senha), nick_reset))
                    conn.commit(); conn.close()
                    st.success(f"✅ Senha de '{nick_reset}' resetada com sucesso!")
        else:
            st.info("Nenhum participante cadastrado ainda.")

    st.divider()
    with st.expander("🗑️ Remover participante"):
        if participants:
            opt = [f"{p['nickname']} — {p['name']}" for p in participants]
            rem = st.selectbox("Selecione", opt)
            if st.button("🗑️ Remover", type="primary"):
                nick = rem.split(" — ")[0]
                conn = get_conn()
                conn.execute("DELETE FROM guesses WHERE nickname=?", (nick,))
                conn.execute("DELETE FROM participants WHERE nickname=?", (nick,))
                conn.commit(); conn.close()
                st.success(f"'{nick}' removido!"); st.rerun()