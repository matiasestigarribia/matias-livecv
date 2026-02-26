/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'dark-deep': 'var(--color-dark-deep)',
        'dark-mid': 'var(--color-dark-mid)',
        'dark-elevated': 'var(--color-dark-elevated)',
        'accent-cyan': 'var(--color-accent-cyan)',
        'accent-purple': 'var(--color-accent-purple)',
        'accent-green': 'var(--color-accent-green)',
        'text-primary': 'var(--color-text-primary)',
        'text-secondary': 'var(--color-text-secondary)',
        'text-tertiary': 'var(--color-text-tertiary)',
      },
    },
  },
  plugins: [],
}