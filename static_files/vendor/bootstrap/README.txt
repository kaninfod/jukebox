Place Bootstrap local assets here, for example:
- bootstrap.min.css
- bootstrap.bundle.min.js (optional, for interactive components)

Recommended version: Bootstrap 5.x
Download from https://getbootstrap.com/ and copy the minified files into this directory.

Once added, include in templates (e.g., in app/web/templates/_global_styles.html):
<link rel="stylesheet" href="/static/vendor/bootstrap/bootstrap.min.css">
<script src="/static/vendor/bootstrap/bootstrap.bundle.min.js" defer></script>

CSP: Local files are served from 'self', so no additional hosts are required.
