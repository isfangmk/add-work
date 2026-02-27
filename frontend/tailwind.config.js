/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f7ff',
          500: '#3498db',
          600: '#2980b9',
          700: '#2c3e50',
        },
        success: '#27ae60',
        error: '#e74c3c',
        warning: '#f39c12',
        gray: {
          50: '#f8f9fa',
          100: '#fafafa',
          500: '#555',
          600: '#666',
          700: '#333',
        }
      },
    },
  },
  plugins: [],
}