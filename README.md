# NovaPay – Django Backend

REST API backend for the NovaPay Digital Banking System.

## Tech Stack
- Python 3.10+
- Django 4.2 + Django REST Framework
- JWT Auth (SimpleJWT)
- SQLite (development)
- SMTP Email (Gmail)

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Register new user |
| POST | `/api/auth/verify-otp/` | No | Verify email OTP |
| POST | `/api/auth/resend-otp/` | No | Resend OTP |
| POST | `/api/auth/login/` | No | Login → JWT tokens |
| POST | `/api/auth/logout/` | Yes | Logout |
| GET  | `/api/auth/profile/` | Yes | Get user profile |
| POST | `/api/auth/change-pin/` | Yes | Change PIN |
| GET  | `/api/banking/balance/` | Yes | Get balance |
| GET  | `/api/banking/transactions/` | Yes | Transaction history |
| POST | `/api/banking/transfer/` | Yes | Transfer funds |
| POST | `/api/banking/withdraw/` | Yes | Withdraw funds |
| POST | `/api/banking/deposit/` | Yes | Deposit (test use) |
| GET  | `/api/banking/validate-account/<acc>/` | Yes | Validate account |

## Setup

### 1. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Edit `.env` file with your Gmail SMTP credentials:
```
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_app_password   # Gmail App Password (not your real password)
```

**How to get Gmail App Password:**
1. Google Account → Security → 2-Step Verification (enable)
2. Security → App Passwords → Create → Select "Mail"
3. Copy the 16-character password into `.env`

### 4. Run migrations
```bash
python manage.py makemigrations accounts banking
python manage.py migrate
```

### 5. Create superuser (for admin panel)
```bash
python manage.py createsuperuser
```

### 6. Start server
```bash
python manage.py runserver
```

Backend runs at **http://localhost:8000**
Admin panel at **http://localhost:8000/admin**

## Testing with Deposit
Since there's no physical cash, use the deposit endpoint to add test money:
```bash
curl -X POST http://localhost:8000/api/banking/deposit/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 50000}'
```

## GitHub Upload
```bash
git init
git add .
git commit -m "feat: Django backend for NovaPay digital banking"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/digital-banking.git
git push -u origin main
```

## Project Structure
```
digital-banking-backend/
├── core/               # Django project settings & URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/           # Auth: register, OTP, login, profile, PIN
│   ├── models.py       # Custom User + OTP models
│   ├── views.py
│   ├── serializers.py
│   ├── utils.py        # OTP generation + email sending
│   └── urls.py
├── banking/            # Core banking: balance, transfer, withdraw
│   ├── models.py       # BankAccount + Transaction models
│   ├── views.py
│   ├── serializers.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── .env                # Your secrets (never commit this!)
```
