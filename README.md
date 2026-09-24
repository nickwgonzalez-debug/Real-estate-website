# Nick Gonzalez — Real Estate Website

One-page site for Nick Gonzalez, Keller Williams, Utah. Plain HTML + CSS, no build step.

- `index.html` — page content (hero, About, Featured Listings, Testimonials, Book a Consultation, Contact)
- `team.html` — Meet the Team page
- `blog.html` — Blog index; posts live in `blog/`
- `styles.css` — styles, including responsive/mobile layout

Open `index.html` in a browser to preview.

## Adding a blog post

1. Copy any file in `blog/`, rename it (e.g. `blog/my-new-post.html`), and edit the title, date, image, and text.
2. Add a matching card at the top of the `.blog-grid` in `blog.html`. The first card is shown large as the featured post.

## Before going live

- Replace the phone number and email in the Contact section.
- Swap the "NG" placeholder in About for a headshot (see the comment in `index.html`).
- Fill in the Meet the Team page (`team.html`): names, roles, bios, photos, and contact info for each teammate.
- Update the listing photos, prices, and details, and the testimonials.
- Connect the booking calendar: in Google Calendar, open your appointment schedule > Share > Website embed, copy the schedule ID from the link, and replace both `YOUR_SCHEDULE_ID` placeholders in `index.html`.
- Require a phone number on bookings: in the appointment schedule's settings under **Booking form**, add a **Phone number** field and mark it required. Google always asks for name and email.
- Connect the Instagram feed: create a free feed widget (e.g. Behold or LightWidget) linked to @nickgonzalezrealtor and paste its embed code into the `.ig-feed` block in `index.html`, replacing the placeholder.
- Point the contact form's `action` at a form service (e.g. Formspree or Netlify Forms) so submissions are delivered.
