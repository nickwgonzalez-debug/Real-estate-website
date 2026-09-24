# Nick Gonzalez — Real Estate Website

One-page site for Nick Gonzalez, Keller Williams, Utah. Plain HTML + CSS, no build step.

- `index.html` — page content (hero, About, Featured Listings, Testimonials, Book a Consultation, Contact)
- `team.html` — Meet the Team page
- `blog.html` — Blog index; posts live in `blog/`
- `styles.css` — styles, including responsive/mobile layout

Open `index.html` in a browser to preview.

## Blog

Posts are written in Markdown in `content/posts/` and built into `blog/`, `blog.html`, and `llms.txt`:

```
python3 scripts/build_blog.py                 # build
python3 scripts/build_blog.py --check FILE    # check length/format rules
```

Don't edit `blog.html` or `blog/*.html` by hand; they are regenerated.

A scheduled routine drafts 10 posts every weekday, emails them for approval, and publishes approved posts. See `content/BLOG_ROUTINE.md`. Facts about Nick used in posts come only from `content/agent-profile.md`.

## Before going live

- Replace the phone number and email in the Contact section.
- Swap the "NG" placeholder in About for a headshot (see the comment in `index.html`).
- Fill in the Meet the Team page (`team.html`): names, roles, bios, photos, and contact info for each teammate.
- Update the listing photos, prices, and details, and the testimonials.
- Connect the booking calendar: in Google Calendar, open your appointment schedule > Share > Website embed, copy the schedule ID from the link, and replace both `YOUR_SCHEDULE_ID` placeholders in `index.html`.
- Require a phone number on bookings: in the appointment schedule's settings under **Booking form**, add a **Phone number** field and mark it required. Google always asks for name and email.
- Connect the Instagram feed: create a free feed widget (e.g. Behold or LightWidget) linked to @nickgonzalezrealtor and paste its embed code into the `.ig-feed` block in `index.html`, replacing the placeholder.
- Fill in `content/agent-profile.md` so "why work with Nick" posts can use real credentials.
- Set `SITE_URL` in `scripts/build_blog.py` and the Sitemap line in `robots.txt` once the domain is live.
- Point the contact form's `action` at a form service (e.g. Formspree or Netlify Forms) so submissions are delivered.
