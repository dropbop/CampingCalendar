# Camping Date Coordinator

A tiny password‑protected event calendar to end the “when can we go?” thread.  
**Public can view. Only you (with a password) can make changes.**

## Stack
- **Frontend:** Vanilla HTML/CSS/JS
- **Backend:** Flask on **Vercel** (serverless)
- **DB:** **Neon** Postgres (managed, serverless-friendly)

## Features
- Read‑only by default; **Unlock** with a password to edit.
- Click dates to mark **Prefer Not** / **No** (or **Clear**).
- Server‑side auth on all write/maintenance routes (can’t be bypassed via client).
