# RockyOS Deployment

This project is set up for direct deployment on a RockyOS server with `nginx`, `systemd`, Next.js, and FastAPI.

## Runtime layout

- `nginx` listens on port `80` or `443`
- Next.js runs on `127.0.0.1:3000`
- FastAPI runs on `127.0.0.1:8000`
- `nginx` proxies `/api`, `/docs`, and `/openapi.json` to FastAPI
- `nginx` proxies all other traffic to Next.js

## 1. Install system packages

```bash
sudo dnf update -y
sudo dnf install -y git nginx python3 python3-pip nodejs rsync
```

If your RockyOS image ships an older Node.js, install Node.js 20 before building the frontend.

## 2. Create an app user

```bash
sudo useradd --system --create-home --shell /bin/bash monthlyfortune
sudo mkdir -p /srv/monthly-fortune
sudo chown -R monthlyfortune:monthlyfortune /srv/monthly-fortune
```

## 3. Clone the project

```bash
sudo -u monthlyfortune git clone <YOUR_REPOSITORY_URL> /srv/monthly-fortune
cd /srv/monthly-fortune
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
```

That value is correct for the recommended single-server deployment.
If you leave `XAI_API_KEY` empty, the app falls back to deterministic monthly interpretations without AI expansion.

## 5. Build and install dependencies

```bash
sudo -u monthlyfortune bash scripts/deploy-rockyos.sh
```

If you want to skip tests during a hotfix deploy:

```bash
sudo -u monthlyfortune RUN_TESTS=0 bash scripts/deploy-rockyos.sh
```

For the very first deploy, the script automatically skips service restarts until the `systemd` units are installed.

## 6. Install systemd units

Copy the template files and adjust the paths or usernames if your server layout is different from `/srv/monthly-fortune` and `monthlyfortune`.

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
sudo vi /srv/monthly-fortune/deploy/rockyos/monthly-fortune.nginx.conf
```

Set:

```nginx
server_name fortune.example.com;
```

Then install and enable it:

```bash
sudo cp deploy/rockyos/monthly-fortune.nginx.conf /etc/nginx/conf.d/monthly-fortune.conf
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
cd /srv/monthly-fortune
sudo -u monthlyfortune git pull
sudo -u monthlyfortune bash scripts/deploy-rockyos.sh
```

## GitHub Actions deployment

After the server is bootstrapped once, GitHub Actions can handle the regular deploys.

Workflow file:

- [`.github/workflows/deploy-rockyos.yml`](/C:/Users/lKira/Project/monthlyFortune/.github/workflows/deploy-rockyos.yml)

### GitHub environment

Create a GitHub Actions environment named `production`.

Add these environment secrets:

- `DEPLOY_HOST`: `donggyu.link`
- `DEPLOY_SSH_KEY`: the private key for `ec2-user`

The workflow deploys as `ec2-user` to `/var/www/python/monthlyFortune`.

It connects over SSH port `22` and scans the server host key during deployment.

### Deploy user permissions

If the deploy user is not `root`, it must be able to restart the services without an interactive password prompt.

Example sudoers entry:

```text
monthlyfortune ALL=NOPASSWD:/usr/bin/systemctl daemon-reload,/usr/bin/systemctl restart monthly-fortune-api,/usr/bin/systemctl restart monthly-fortune-web,/usr/bin/systemctl reload nginx
```

Create it with:

```bash
sudo visudo -f /etc/sudoers.d/monthly-fortune-deploy
```

### How the workflow deploys

1. GitHub Actions runs lint, build, and Python tests on `ubuntu-latest`.
2. If CI passes, it syncs the repository to the RockyOS server with `rsync`.
3. It runs `scripts/deploy-rockyos.sh` on the server.
4. It reloads `systemd`, restarts the app services, and reloads `nginx`.

## Notes

- The current frontend uses server-side fetches, so `MONTHLY_FORTUNE_API_URL=http://127.0.0.1:8000` works well when both services run on the same server.
- The included `docker-compose.yml` is no longer the primary deployment path.
- If you add HTTPS with Certbot later, keep the upstream targets on `127.0.0.1:3000` and `127.0.0.1:8000`.
