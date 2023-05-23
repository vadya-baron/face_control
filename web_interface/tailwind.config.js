/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./admin/*.html', './detector/*.html', './node_modules/tw-elements/dist/js/**/*.js'],
  theme: {
    backgroundColor: theme => ({
       ...theme('colors'),
       'primary': 'rgba(31,41,55, 1)',
       'secondary': '#ffed4a',
       'danger': '#e3342f',
      }),
    extend: {},
  },
  plugins: [],
}

