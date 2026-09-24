# Nick Gonzalez — Real Estate Website

One-page site for Nick Gonzalez, Keller Williams, Utah. Plain HTML + CSS, no build step.

- `index.html` — page content (hero, About, Featured Listings, Testimonials, Book a Consultation, Contact)
- `styles.css` — styles, including responsive/mobile layout

Open `index.html` in a browser to preview.

## Before going live

- Replace the phone number and email in the Contact section.
- Swap the "NG" placeholder in About for a headshot (see the comment in `index.html`).
- Update the listing photos, prices, and details, and the testimonials.
- Connect the booking calendar: in Google Calendar, open your appointment schedule > Share > Website embed, copy the schedule ID from the link, and replace both `YOUR_SCHEDULE_ID` placeholders in `index.html`.
- Require a phone number on bookings: in the appointment schedule's settings under **Booking form**, add a **Phone number** field and mark it required. Google always asks for name and email.
- Point the contact form's `action` at a form service (e.g. Formspree or Netlify Forms) so submissions are delivered.
