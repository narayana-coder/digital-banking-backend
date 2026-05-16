from django.core.mail import send_mail
from django.conf import settings


def send_transaction_email(user, transaction_type, amount, balance_after, reference_id='', recipient_name='', sender_name='', source='Cash Deposit'):
    amount_str = f"Rs.{float(amount):,.2f}"
    balance_str = f"Rs.{float(balance_after):,.2f}"

    if transaction_type == 'withdrawal':
        subject = f"NovaPay - Withdrawal of {amount_str} Successful"
        action_color = "#ff4d6d"
        action_label = "WITHDRAWN"
        action_sign = "-"
        detail_line = f"<tr><td style='color:#8ba3c7;padding:10px 0'>Description</td><td style='text-align:right;font-weight:600'>Cash Withdrawal</td></tr>"
    elif transaction_type == 'deposit':
        subject = f"NovaPay - Deposit of {amount_str} Successful"
        action_color = "#00d4aa"
        action_label = "DEPOSITED"
        action_sign = "+"
        detail_line = f"<tr><td style='color:#8ba3c7;padding:10px 0'>Source</td><td style='text-align:right;font-weight:600'>{source}</td></tr>"
    elif transaction_type == 'transfer_debit':
        subject = f"NovaPay - Transfer of {amount_str} to {recipient_name}"
        action_color = "#ff4d6d"
        action_label = "TRANSFERRED"
        action_sign = "-"
        detail_line = f"<tr><td style='color:#8ba3c7;padding:10px 0'>To</td><td style='text-align:right;font-weight:600'>{recipient_name}</td></tr>"
    elif transaction_type == 'transfer_credit':
        subject = f"NovaPay - You received {amount_str} from {sender_name}"
        action_color = "#00d4aa"
        action_label = "RECEIVED"
        action_sign = "+"
        detail_line = f"<tr><td style='color:#8ba3c7;padding:10px 0'>From</td><td style='text-align:right;font-weight:600'>{sender_name}</td></tr>"
    else:
        subject = f"NovaPay - Transaction Notification"
        action_color = "#00d4aa"
        action_label = "CREDITED"
        action_sign = "+"
        detail_line = ""

    html_message = f"""
<div style="font-family:'Segoe UI',sans-serif;max-width:520px;margin:auto;background:#0a1628;border-radius:16px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#0f3460,#162843);padding:28px 32px;border-bottom:1px solid #1e3a5f;">
    <span style="color:#00d4aa;font-size:1.3rem;font-weight:700;">&#127974; NovaPay</span>
    <p style="color:#8ba3c7;margin:8px 0 0;font-size:0.85rem;">Transaction Notification</p>
  </div>
  <div style="padding:28px 32px;">
    <p style="color:#8ba3c7;">Hello <strong style="color:#e8f0fe;">{user.full_name}</strong>,</p>
    <p style="color:#8ba3c7;margin-bottom:24px;">A transaction has been processed on your account.</p>
    <div style="background:#162843;border:1px solid #1e3a5f;border-radius:12px;padding:24px;text-align:center;margin-bottom:20px;">
      <div style="color:#8ba3c7;font-size:0.72rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">{action_label}</div>
      <div style="font-size:2rem;font-weight:700;color:{action_color};">{action_sign}{amount_str}</div>
    </div>
    <table style="width:100%;border-collapse:collapse;color:#e8f0fe;font-size:0.88rem;">
      <tr style="border-bottom:1px solid #1e3a5f;">
        <td style="color:#8ba3c7;padding:10px 0">Account</td>
        <td style="text-align:right;font-family:monospace;font-weight:600;">{user.account_number}</td>
      </tr>
      {detail_line}
      <tr style="border-bottom:1px solid #1e3a5f;">
        <td style="color:#8ba3c7;padding:10px 0">Reference ID</td>
        <td style="text-align:right;font-family:monospace;font-size:0.8rem;">{reference_id}</td>
      </tr>
      <tr>
        <td style="color:#8ba3c7;padding:10px 0">Balance After</td>
        <td style="text-align:right;font-weight:700;color:#00d4aa;">{balance_str}</td>
      </tr>
    </table>
    <div style="margin-top:20px;background:#162843;border-left:3px solid #00d4aa;border-radius:4px;padding:12px 16px;font-size:0.8rem;color:#8ba3c7;">
      If you did not authorize this transaction, contact NovaPay support immediately.
    </div>
  </div>
  <div style="padding:16px 32px;border-top:1px solid #1e3a5f;text-align:center;">
    <p style="color:#4a6080;font-size:0.72rem;margin:0;">© 2026 NovaPay Digital Banking. Automated notification.</p>
  </div>
</div>
"""
    plain = f"NovaPay | {action_label}: {action_sign}{amount_str} | Balance: {balance_str} | Ref: {reference_id}"

    try:
        send_mail(subject, plain, settings.DEFAULT_FROM_EMAIL, [user.email], html_message=html_message, fail_silently=False)
        print(f"[EMAIL SENT] {transaction_type} -> {user.email}")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
