import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
import pytz

# ══════════════════════════════════════════════
#  CONFIGURAÇÕES — EDITE AQUI ANTES DE PUBLICAR
# ══════════════════════════════════════════════
ADMIN_PASSWORD   = "copa2026admin"   # ← Troque por uma senha segura
INVITE_CODE      = "copa2026"        # ← Código que você vai enviar aos convidados
DB_PATH          = "bolao.db"

# Prazo final para palpites: 10 de junho de 2026 às 23h59 (horário de Brasília)
DEADLINE = datetime(2026, 6, 10, 23, 59, 0)
TZ_BR    = pytz.timezone("America/Sao_Paulo")

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

def get_all_matches():
    matches = []
    match_id = 1
    for g, teams in GROUPS.items():
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matches.append({"id": match_id, "group": g, "home": teams[i], "away": teams[j]})
                match_id += 1
    return matches

ALL_MATCHES  = get_all_matches()
MATCH_BY_ID  = {m["id"]: m for m in ALL_MATCHES}

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            nickname   TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS guesses (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nickname         TEXT NOT NULL,
            match_id         INTEGER NOT NULL,
            home_goals       INTEGER NOT NULL,
            away_goals       INTEGER NOT NULL,
            submitted_at     TEXT DEFAULT (datetime('now')),
            UNIQUE(nickname, match_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS results (
            match_id   INTEGER PRIMARY KEY,
            home_goals INTEGER NOT NULL,
            away_goals INTEGER NOT NULL,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ══════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def is_deadline_passed():
    now = datetime.now(TZ_BR).replace(tzinfo=None)
    return now > DEADLINE

def deadline_str():
    return DEADLINE.strftime("%d/%m/%Y às %H:%M") + " (Brasília)"

# ══════════════════════════════════════════════
#  FUNÇÕES DE BANCO
# ══════════════════════════════════════════════
def register_user(name, nickname, password):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO participants (name, nickname, password) VALUES (?, ?, ?)",
            (name.strip(), nickname.strip().lower(), hash_pw(password))
        )
        conn.commit()
        conn.close()
        return True, "Cadastro realizado com sucesso!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Este apelido já está em uso. Escolha outro."

def login_user(nickname, password):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM participants WHERE nickname=? AND password=?",
        (nickname.strip().lower(), hash_pw(password))
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def save_guesses_batch(nickname, guesses_dict):
    """guesses_dict: {match_id: (home, away)}"""
    conn = get_conn()
    for mid, (h, a) in guesses_dict.items():
        conn.execute("""
            INSERT INTO guesses (nickname, match_id, home_goals, away_goals)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(nickname, match_id) DO UPDATE SET
                home_goals=excluded.home_goals,
                away_goals=excluded.away_goals,
                submitted_at=datetime('now')
        """, (nickname, mid, h, a))
    conn.commit()
    conn.close()

def get_guesses(nickname):
    conn = get_conn()
    rows = conn.execute(
        "SELECT match_id, home_goals, away_goals FROM guesses WHERE nickname=?",
        (nickname,)
    ).fetchall()
    conn.close()
    return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in rows}

def get_all_guesses():
    conn = get_conn()
    rows = conn.execute("SELECT nickname, match_id, home_goals, away_goals FROM guesses").fetchall()
    conn.close()
    return rows

def save_result(match_id, home, away):
    conn = get_conn()
    conn.execute("""
        INSERT INTO results (match_id, home_goals, away_goals)
        VALUES (?, ?, ?)
        ON CONFLICT(match_id) DO UPDATE SET
            home_goals=excluded.home_goals,
            away_goals=excluded.away_goals,
            updated_at=datetime('now')
    """, (match_id, home, away))
    conn.commit()
    conn.close()

def get_results():
    conn = get_conn()
    rows = conn.execute("SELECT match_id, home_goals, away_goals FROM results").fetchall()
    conn.close()
    return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in rows}

def get_all_participants():
    conn = get_conn()
    rows = conn.execute("SELECT name, nickname, created_at FROM participants ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ══════════════════════════════════════════════
#  PONTUAÇÃO
# ══════════════════════════════════════════════
def calc_result(h, a):
    if h > a: return "H"
    if h < a: return "A"
    return "E"

def calc_points(gh, ga, rh, ra):
    pts, detail = 0, []
    if gh == rh and ga == ra:
        pts += 5
        detail.append("✅ Placar exato (+5)")
    elif calc_result(gh, ga) == calc_result(rh, ra):
        pts += 3
        detail.append("🏆 Resultado certo (+3)")
    if not (gh == rh and ga == ra):
        if gh == rh or ga == ra:
            pts += 1
            detail.append("⚽ Gols de um time (+1)")
    return pts, detail

def calc_ranking():
    results  = get_results()
    guesses  = get_all_guesses()
    scores   = {}
    details  = {}
    for row in guesses:
        nick = row["nickname"]
        mid  = row["match_id"]
        if mid not in results:
            continue
        pts, det = calc_points(row["home_goals"], row["away_goals"], *results[mid])
        scores[nick]  = scores.get(nick, 0) + pts
        details.setdefault(nick, []).append({"match_id": mid, "pts": pts, "detail": det})
    return scores, details

# ══════════════════════════════════════════════
#  PÁGINA CONFIG
# ══════════════════════════════════════════════
st.set_page_config(page_title="Bolão Copa 2026", page_icon="⚽", layout="wide")

st.markdown("""
<style>
    .group-pill {
        display:inline-block;
        background:#1a6b3a;color:#fff;
        padding:4px 14px;border-radius:20px;
        font-weight:600;font-size:14px;margin-bottom:8px;
    }
    .deadline-box {
        background:#fff3cd;border-left:4px solid #ffc107;
        padding:10px 14px;border-radius:4px;font-size:14px;margin-bottom:12px;
    }
    .locked-box {
        background:#f8d7da;border-left:4px solid #dc3545;
        padding:10px 14px;border-radius:4px;font-size:14px;margin-bottom:12px;
    }
    .success-box {
        background:#d4edda;border-left:4px solid #28a745;
        padding:10px 14px;border-radius:4px;font-size:14px;margin-bottom:12px;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════
if "user" not in st.session_state:
    st.session_state.user = None
if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"   # "login" | "register"

# ══════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚽ Bolão Copa 2026")
    if st.session_state.user:
        st.success(f"👤 **{st.session_state.user['nickname']}**\n\n{st.session_state.user['name']}")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    st.divider()

    if st.session_state.user or st.session_state.admin_logged:
        page = st.radio("Navegação", [
            "🏠 Início",
            "📝 Meus Palpites",
            "🏆 Ranking",
            "📊 Resultados",
            "🔐 Admin"
        ])
    else:
        page = "🏠 Início"

    st.divider()
    st.markdown("""
    **Pontuação:**
    - ✅ Placar exato → **5 pts**
    - 🏆 Resultado certo → **3 pts**
    - ⚽ Gols de 1 time → **+1 pt**
    """)
    locked = is_deadline_passed()
    if locked:
        st.markdown(f'<div class="locked-box">🔒 <b>Palpites encerrados</b><br>{deadline_str()}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="deadline-box">⏰ <b>Prazo:</b><br>{deadline_str()}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  PÁGINA: INÍCIO / LOGIN / CADASTRO
# ══════════════════════════════════════════════
if page == "🏠 Início":
    st.markdown("# ⚽ Bolão Copa do Mundo 2026")

    if st.session_state.user:
        u = st.session_state.user
        st.markdown(f'<div class="success-box">Bem-vindo de volta, <b>{u["name"]}</b>! Use o menu lateral para fazer seus palpites.</div>', unsafe_allow_html=True)
        scores, _ = calc_ranking()
        results   = get_results()
        participants = get_all_participants()
        c1, c2, c3 = st.columns(3)
        c1.metric("👥 Participantes", len(participants))
        c2.metric("⚽ Jogos com resultado", len(results))
        c3.metric("📊 Seus pontos", scores.get(u["nickname"], 0))

    else:
        col1, col2 = st.columns([1, 1], gap="large")

        # ── LOGIN ──
        with col1:
            st.markdown("### 🔑 Entrar")
            if st.session_state.auth_page == "login":
                nick_l = st.text_input("Apelido", key="login_nick", placeholder="seu apelido")
                pw_l   = st.text_input("Senha",   key="login_pw",   type="password")
                if st.button("Entrar", use_container_width=True, type="primary"):
                    if nick_l and pw_l:
                        user = login_user(nick_l, pw_l)
                        if user:
                            st.session_state.user = user
                            st.rerun()
                        else:
                            st.error("Apelido ou senha incorretos.")
                    else:
                        st.warning("Preencha todos os campos.")
                st.markdown("Não tem cadastro? →")
                if st.button("Criar conta", use_container_width=True):
                    st.session_state.auth_page = "register"
                    st.rerun()

        # ── CADASTRO ──
        with col2:
            st.markdown("### 📋 Criar conta")
            if st.session_state.auth_page == "register":
                invite  = st.text_input("Código de convite", key="reg_invite", placeholder="código enviado pelo organizador")
                name_r  = st.text_input("Nome completo",     key="reg_name")
                nick_r  = st.text_input("Apelido",           key="reg_nick",   placeholder="como aparece no ranking")
                pw_r    = st.text_input("Senha",             key="reg_pw",     type="password")
                pw_r2   = st.text_input("Confirmar senha",   key="reg_pw2",    type="password")

                if st.button("Cadastrar", use_container_width=True, type="primary"):
                    if not all([invite, name_r, nick_r, pw_r, pw_r2]):
                        st.error("Preencha todos os campos.")
                    elif invite.strip().lower() != INVITE_CODE.lower():
                        st.error("Código de convite inválido.")
                    elif pw_r != pw_r2:
                        st.error("As senhas não coincidem.")
                    elif len(pw_r) < 4:
                        st.error("Senha deve ter ao menos 4 caracteres.")
                    else:
                        ok, msg = register_user(name_r, nick_r, pw_r)
                        if ok:
                            user = login_user(nick_r, pw_r)
                            st.session_state.user = user
                            st.session_state.auth_page = "login"
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                st.markdown("Já tem conta? →")
                if st.button("Fazer login", use_container_width=True):
                    st.session_state.auth_page = "login"
                    st.rerun()
            else:
                st.info("Clique em **Criar conta** ao lado para se cadastrar com seu código de convite.")

# ══════════════════════════════════════════════
#  PÁGINA: MEUS PALPITES
# ══════════════════════════════════════════════
elif page == "📝 Meus Palpites":
    if not st.session_state.user:
        st.warning("Faça login para acessar seus palpites.")
        st.stop()

    user    = st.session_state.user
    locked  = is_deadline_passed()

    st.markdown(f"# 📝 Palpites de **{user['nickname']}**")

    if locked:
        st.markdown('<div class="locked-box">🔒 <b>Prazo encerrado.</b> Os palpites estão bloqueados. Você ainda pode consultar o que enviou.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="deadline-box">⏰ Preencha todos os jogos e clique em <b>Confirmar e Salvar</b> no final. Prazo: <b>{deadline_str()}</b></div>', unsafe_allow_html=True)

    my_guesses = get_guesses(user["nickname"])
    results    = get_results()

    # Coleta todos os palpites em um dicionário temporário por grupo
    all_inputs = {}

    for g, teams in GROUPS.items():
        matches_in_group = [m for m in ALL_MATCHES if m["group"] == g]
        with st.expander(f"🏟️ Grupo {g}  —  {' · '.join(teams)}", expanded=False):
            for match in matches_in_group:
                mid  = match["id"]
                existing = my_guesses.get(mid, (0, 0))
                real     = results.get(mid)

                c1, c2, c3, c4, c5 = st.columns([3, 1.2, 0.3, 1.2, 3])
                with c1:
                    st.markdown(f"<div style='text-align:right;padding-top:6px;font-size:13px;'>{match['home']}</div>", unsafe_allow_html=True)
                with c2:
                    h = st.number_input("", min_value=0, max_value=20,
                        value=int(existing[0]),
                        key=f"g_h_{mid}",
                        label_visibility="collapsed",
                        disabled=locked)
                with c3:
                    st.markdown("<div style='text-align:center;padding-top:6px;color:#aaa;'>×</div>", unsafe_allow_html=True)
                with c4:
                    a = st.number_input("", min_value=0, max_value=20,
                        value=int(existing[1]),
                        key=f"g_a_{mid}",
                        label_visibility="collapsed",
                        disabled=locked)
                with c5:
                    st.markdown(f"<div style='padding-top:6px;font-size:13px;'>{match['away']}</div>", unsafe_allow_html=True)

                # Se já há resultado, mostra pontuação
                if real:
                    pts, det = calc_points(h, a, real[0], real[1])
                    det_str = " | ".join(det) if det else "0 pontos"
                    st.markdown(f"<div style='text-align:center;font-size:11px;color:#777;margin-bottom:4px;'>Resultado real: {real[0]}×{real[1]} — {det_str}</div>", unsafe_allow_html=True)

                all_inputs[mid] = (h, a)

    st.divider()
    if not locked:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("✅ Confirmar e Salvar TODOS os palpites", type="primary", use_container_width=True):
                save_guesses_batch(user["nickname"], all_inputs)
                st.success(f"✅ {len(all_inputs)} palpites salvos com sucesso!")
                st.balloons()
    else:
        total_sent = len(my_guesses)
        st.info(f"Você enviou palpites para **{total_sent}** de **{len(ALL_MATCHES)}** jogos.")

# ══════════════════════════════════════════════
#  PÁGINA: RANKING
# ══════════════════════════════════════════════
elif page == "🏆 Ranking":
    st.markdown("# 🏆 Ranking do Bolão")

    scores, details = calc_ranking()
    participants    = get_all_participants()

    if not participants:
        st.info("Nenhum participante cadastrado ainda.")
        st.stop()

    all_scores    = {p["nickname"]: scores.get(p["nickname"], 0) for p in participants}
    sorted_scores = sorted(all_scores.items(), key=lambda x: -x[1])
    nick_to_name  = {p["nickname"]: p["name"] for p in participants}

    medals = ["🥇", "🥈", "🥉"]
    rows   = []
    for i, (nick, pts) in enumerate(sorted_scores):
        medal = medals[i] if i < 3 else f"{i+1}º"
        rows.append({"Pos": medal, "Apelido": nick, "Nome": nick_to_name.get(nick, ""), "Pontos": pts})

    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, use_container_width=True,
                 column_config={
                     "Pos":    st.column_config.TextColumn(width="small"),
                     "Pontos": st.column_config.NumberColumn(format="%d pts"),
                 })

    st.divider()
    st.markdown("### 🔍 Detalhes por participante")
    results  = get_results()
    options  = [f"{nick} ({nick_to_name.get(nick,'')})" for nick, _ in sorted_scores]
    selected = st.selectbox("Escolha um participante", options)

    if selected:
        sel_nick    = selected.split(" (")[0]
        my_guesses  = get_guesses(sel_nick)
        total       = 0
        detail_rows = []
        for mid, (rh, ra) in results.items():
            match = MATCH_BY_ID.get(mid)
            if not match:
                continue
            if mid in my_guesses:
                gh, ga   = my_guesses[mid]
                pts, det = calc_points(gh, ga, rh, ra)
                total   += pts
                detail_rows.append({
                    "Grupo":   f"Grupo {match['group']}",
                    "Jogo":    f"{match['home']} × {match['away']}",
                    "Palpite": f"{gh}×{ga}",
                    "Real":    f"{rh}×{ra}",
                    "Pontos":  pts,
                    "Detalhe": " | ".join(det) if det else "—"
                })
            else:
                detail_rows.append({
                    "Grupo":   f"Grupo {match['group']}",
                    "Jogo":    f"{match['home']} × {match['away']}",
                    "Palpite": "—",
                    "Real":    f"{rh}×{ra}",
                    "Pontos":  0,
                    "Detalhe": "Sem palpite"
                })

        if detail_rows:
            st.markdown(f"**Total: {total} pontos**")
            st.dataframe(pd.DataFrame(detail_rows), hide_index=True, use_container_width=True)
        else:
            st.info("Nenhum resultado lançado ainda.")

# ══════════════════════════════════════════════
#  PÁGINA: RESULTADOS
# ══════════════════════════════════════════════
elif page == "📊 Resultados":
    st.markdown("# 📊 Resultados dos Jogos")
    results = get_results()

    if not results:
        st.info("Nenhum resultado lançado ainda. Aguarde o admin lançar os placares.")
    else:
        rows = []
        for mid, (rh, ra) in sorted(results.items()):
            match = MATCH_BY_ID.get(mid)
            if match:
                if rh > ra:   res = f"🟢 {match['home']}"
                elif rh < ra: res = f"🔴 {match['away']}"
                else:         res = "🔵 Empate"
                rows.append({
                    "Grupo": f"Grupo {match['group']}",
                    "Casa":  match["home"],
                    "Placar": f"{rh} × {ra}",
                    "Fora":  match["away"],
                    "Vencedor": res,
                })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

# ══════════════════════════════════════════════
#  PÁGINA: ADMIN
# ══════════════════════════════════════════════
elif page == "🔐 Admin":
    st.markdown("# 🔐 Painel do Administrador")

    if not st.session_state.admin_logged:
        pwd = st.text_input("Senha de administrador", type="password")
        if st.button("Entrar como admin"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
        st.stop()

    st.success("✅ Logado como administrador")
    if st.button("Sair do admin"):
        st.session_state.admin_logged = False
        st.rerun()

    # ── Info do bolão ──
    st.divider()
    st.markdown("### ⚙️ Configurações atuais")
    col1, col2, col3 = st.columns(3)
    col1.info(f"**Código de convite:**\n\n`{INVITE_CODE}`")
    col2.info(f"**Prazo de palpites:**\n\n{deadline_str()}")
    col3.info(f"**Status:**\n\n{'🔒 Encerrado' if is_deadline_passed() else '🟢 Aberto'}")

    # ── Lançar resultados ──
    st.divider()
    st.markdown("### ⚽ Lançar Resultados")
    results   = get_results()
    group_sel = st.selectbox("Selecione o grupo", list(GROUPS.keys()), format_func=lambda g: f"Grupo {g}")
    matches_in_group = [m for m in ALL_MATCHES if m["group"] == group_sel]

    for match in matches_in_group:
        mid      = match["id"]
        existing = results.get(mid, (0, 0))
        c1, c2, c3, c4, c5, c6 = st.columns([3, 1.2, 0.3, 1.2, 3, 1.5])
        with c1:
            st.markdown(f"<div style='text-align:right;padding-top:6px;font-size:13px;'>{match['home']}</div>", unsafe_allow_html=True)
        with c2:
            rh = st.number_input("", min_value=0, max_value=20, value=int(existing[0]), key=f"r_h_{mid}", label_visibility="collapsed")
        with c3:
            st.markdown("<div style='text-align:center;padding-top:6px;color:#aaa;'>×</div>", unsafe_allow_html=True)
        with c4:
            ra = st.number_input("", min_value=0, max_value=20, value=int(existing[1]), key=f"r_a_{mid}", label_visibility="collapsed")
        with c5:
            st.markdown(f"<div style='padding-top:6px;font-size:13px;'>{match['away']}</div>", unsafe_allow_html=True)
        with c6:
            if st.button("💾 Salvar", key=f"sr_{mid}"):
                save_result(mid, rh, ra)
                st.success("Salvo!")
                st.rerun()

    # ── Participantes ──
    st.divider()
    st.markdown("### 👥 Participantes cadastrados")
    participants = get_all_participants()
    if participants:
        df_p = pd.DataFrame([{
            "Nome": p["name"],
            "Apelido": p["nickname"],
            "Cadastro": p["created_at"],
            "Palpites": len(get_guesses(p["nickname"]))
        } for p in participants])
        st.dataframe(df_p, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum participante ainda.")

    # ── Remover participante ──
    st.divider()
    with st.expander("🗑️ Remover participante"):
        if participants:
            options   = [f"{p['nickname']} — {p['name']}" for p in participants]
            to_remove = st.selectbox("Selecione", options)
            if st.button("🗑️ Remover participante e todos os palpites", type="primary"):
                nick = to_remove.split(" — ")[0]
                conn = get_conn()
                conn.execute("DELETE FROM guesses WHERE nickname=?",      (nick,))
                conn.execute("DELETE FROM participants WHERE nickname=?", (nick,))
                conn.commit()
                conn.close()
                st.success(f"Participante '{nick}' removido!")
                st.rerun()
