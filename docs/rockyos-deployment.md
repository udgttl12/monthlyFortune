# OCI Oracle Linux Deployment

This project is set up for direct deployment on an OCI Oracle Linux server with `nginx`, `systemd`, Next.js, and FastAPI.

## Runtime layout

- `nginx` listens on port `80` or `443`
- Next.js runs on `127.0.0.1:3000`
- FastAPI runs on `127.0.0.1:8000`
- `nginx` proxies `/api`, `/docs`, and `/openapi.json` to FastAPI
- `nginx` proxies all other traffic to Next.js

## 1. Install system packages

```bash
sudo dnf update -y
sudo dnf install -y nginx python3 python3-pip nodejs rsync
```

Install Node.js 20 or newer before building the frontend.

## 2. Create an app user

```bash
sudo install -d -m 755 -o opc -g opc /var/www/python/monthlyFortune
```

## 3. Clone the project

```bash
git clone <YOUR_REPOSITORY_URL> /var/www/python/monthlyFortune
cd /var/www/python/monthlyFortune
```

## 4. Create the frontend environment file

```bash
cp .env.production.example .env.production
```

Default value:

```dotenv
MONTHLY_FORTUNE_API_URL=http://127.0.0.1:8000
XAI_API_KEY=
XAI_MODEL=grok-4.20-reasoning
XAI_TIMEOUT_SECONDS=45
MONTHLY_LLM_PROVIDER=xai
UPSTAGE_API_KEY=
UPSTAGE_API_BASE_URL=https://api.upstage.ai/v1
UPSTAGE_MODEL=solar-pro3
UPSTAGE_REASONING_EFFORT=
```

That value is correct for the recommended single-server deployment.
If you leave `XAI_API_KEY` empty, the app falls back to deterministic monthly interpretations without AI expansion.

`MONTHLY_LLM_PROVIDER` selects the provider for the monthly horoscope report (`xai` or `upstage`).
It defaults to `xai` and reads the legacy `XAI_*` variables, so existing deployments keep working unchanged.
Set it to `upstage` together with `UPSTAGE_API_KEY` to route the monthly report through Upstage Solar.
The AI retention loop has its own switch, `LLM_RETENTION_PROVIDER`, which also accepts `upstage`.
Changing either provider invalidates the matching cache entries by design, so the first requests after a switch recompute.

## 5. Build and install dependencies

```bash
bash scripts/deploy-rockyos.sh
```

If you want to skip tests during a hotfix deploy:

```bash
RUN_TESTS=0 bash scripts/deploy-rockyos.sh
```

For the very first deploy, the script automatically skips service restarts until the `systemd` units are installed.

## 6. Install systemd units

Copy the template files. The OCI server should run them as `opc`.

```bash
sudo cp deploy/rockyos/monthly-fortune-api.service /etc/systemd/system/
sudo cp deploy/rockyos/monthly-fortune-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now monthly-fortune-api
sudo systemctl enable --now monthly-fortune-web
```

## 7. Install the nginx site

Edit the server name first:

```bash
sudo vi /var/www/python/monthlyFortune/deploy/rockyos/monthly-fortune.nginx.conf
```

Set:

```nginx
server_name donggyu.link;
```

Then install and enable it:

```bash
sudo cp deploy/rockyos/monthly-fortune.nginx.conf /etc/nginx/conf.d/donggyu.link.conf
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

## 8. Recommended firewall rules

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 9. Check service status

```bash
sudo systemctl status monthly-fortune-api
sudo systemctl status monthly-fortune-web
sudo systemctl status nginx
```

Useful logs:

```bash
sudo journalctl -u monthly-fortune-api -n 100 --no-pager
sudo journalctl -u monthly-fortune-web -n 100 --no-pager
sudo journalctl -u nginx -n 100 --no-pager
```

## Updating the server

```bash
cd /var/www/python/monthlyFortune
git pull
bash scripts/deploy-rockyos.sh
```

## GitHub Actions deployment

After the server is bootstrapped once, GitHub Actions handles regular deploys only. It syncs the app, installs Python runtime dependencies, restarts the existing services, and runs localhost health checks. It does not install or enable systemd units and does not change nginx.

Workflow file:

- [`.github/workflows/deploy-rockyos.yml`](/C:/Users/lKira/Project/monthlyFortune/.github/workflows/deploy-rockyos.yml)

### GitHub environment

Create a GitHub Actions environment named `production`.

Add these environment secrets:

- `DEPLOY_HOST`: the OCI host IP or a DNS name that already points to it
- `DEPLOY_SSH_KEY`: the private key for `opc`
- `DEPLOY_KNOWN_HOSTS`: output of `ssh-keyscan -H <DEPLOY_HOST>`

The workflow deploys as `opc` to `/var/www/python/monthlyFortune`.

It connects over SSH port `22` and scans the server host key during deployment.

### Deploy user permissions

The `opc` user must be able to restart the services without an interactive password prompt.

Example sudoers entry:

```text
opc ALL=NOPASSWD:/usr/bin/systemctl restart monthly-fortune-api,/usr/bin/systemctl restart monthly-fortune-web
```

Create it with:

```bash
sudo visudo -f /etc/sudoers.d/monthly-fortune-deploy
```

### How the workflow deploys

1. GitHub Actions runs lint, build, and Python tests on `ubuntu-latest`.
2. If CI passes, it syncs the repository to the OCI server with `rsync`.
3. It runs `scripts/deploy-rockyos.sh` on the server with tests and frontend rebuild disabled.
4. It restarts `monthly-fortune-api` and `monthly-fortune-web`.
5. It checks `http://127.0.0.1:8000/docs` and `http://127.0.0.1:3000` on the server.

## Notes

- The current frontend uses server-side fetches, so `MONTHLY_FORTUNE_API_URL=http://127.0.0.1:8000` works well when both services run on the same server.
- The included `docker-compose.yml` is no longer the primary deployment path.
- If you add HTTPS with Certbot later, keep the upstream targets on `127.0.0.1:3000` and `127.0.0.1:8000`.
