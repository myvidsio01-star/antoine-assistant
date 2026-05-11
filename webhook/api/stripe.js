import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const event = req.body;

  // On traite uniquement les paiements réussis via Payment Link
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const email = session.customer_details?.email;

    if (!email) return res.status(200).json({ received: true });

    await resend.emails.send({
      from: 'A.N.T.O.I.N.E <noreply@resend.dev>',
      to: email,
      subject: '🎙️ Votre accès A.N.T.O.I.N.E V1.1 — Téléchargement',
      html: `
        <div style="font-family:Inter,sans-serif;background:#06070d;color:#e2e8f0;padding:40px;max-width:560px;margin:0 auto;border-radius:16px;">
          <h1 style="color:#00c8ff;font-size:24px;margin-bottom:8px;">Merci pour votre achat !</h1>
          <p style="color:#94a3b8;margin-bottom:32px;">Votre accès à A.N.T.O.I.N.E V1.1 est prêt.</p>

          <a href="https://myvidsio01-star.github.io/antoine-assistant/premium.html"
             style="display:inline-block;background:#00c8ff;color:#000;font-weight:800;padding:14px 28px;border-radius:10px;text-decoration:none;font-size:16px;margin-bottom:32px;">
            ⬇ Télécharger ANTOINE V1.1
          </a>

          <div style="background:#0d0f1a;border:1px solid rgba(0,200,255,0.15);border-radius:12px;padding:20px;margin-bottom:24px;">
            <p style="font-weight:700;margin-bottom:12px;">Installation en 3 étapes :</p>
            <ol style="color:#94a3b8;padding-left:20px;line-height:2;">
              <li>Décompressez <code style="color:#00c8ff;">ANTOINE-V1.1.zip</code></li>
              <li>Renommez <code style="color:#00c8ff;">.env.example</code> en <code style="color:#00c8ff;">.env</code> et ajoutez votre clé Groq gratuite (<a href="https://console.groq.com" style="color:#00c8ff;">console.groq.com</a>)</li>
              <li>Double-cliquez <code style="color:#00c8ff;">ANTOINE.exe</code> et dites <strong style="color:#e2e8f0;">"Hey Antoine"</strong> 🎙️</li>
            </ol>
          </div>

          <p style="color:#64748b;font-size:13px;">
            Un problème ? Rejoignez le Discord :
            <a href="https://discord.gg/JP9yF3VWQ" style="color:#8b9cf4;">discord.gg/JP9yF3VWQ</a>
          </p>
        </div>
      `
    });
  }

  res.status(200).json({ received: true });
}
