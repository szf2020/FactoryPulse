# FactoryPulse - Industrial IoT Dashboard (Frontend)

## Overview

FactoryPulse is a comprehensive Industry 4.0 dashboard designed to monitor industrial machinery in real-time. This frontend application provides an intuitive interface for visualizing telemetry data, tracking Overall Equipment Effectiveness (OEE), managing alerts, and generating production reports.

The application is built with a focus on performance, scalability, and user experience, featuring dynamic theming (Dark/Light modes), internationalization (i18n), and responsive data visualization.

## Key Features

* **Real-Time Dashboard:** High-level overview of factory operations, including active machines, total energy consumption, and aggregated OEE statistics.
* **Machine Telemetry:** Detailed individual machine views with real-time line charts visualizing energy consumption (Amps) and operational status.
* **OEE Calculation:** Automatic display of Availability, Performance, and Quality metrics based on backend data.
* **Dynamic Data Visualization:** Interactive charts powered by Chart.js, supporting different time ranges (1 Hour, 24 Hours, 7 Days).
* **Internationalization (i18n):** Full support for Portuguese (PT), English (EN), and Spanish (ES) with instant language switching.
* **Theme System:** Built-in Dark and Light modes with persistent state management via LocalStorage.
* **Authentication:** Secure Login and Registration flows using JWT (JSON Web Tokens) with automatic session restoration.
* **Responsive Design:** Fully adaptive layout optimized for desktop, tablet, and mobile devices.

## Technology Stack

This project leverages modern web development technologies to ensure maintainability and performance:

* **Core:** React.js
* **Styling:** Tailwind CSS
* **State Management:** React Context API (AuthContext, AppContext)
* **Routing:** React Router DOM
* **HTTP Client:** Axios (with Interceptors for JWT handling)
* **Charts:** Chart.js and react-chartjs-2
* **Icons:** Lucide React
* **Build Tool:** Vite (or Create React App, depending on your setup)

## Project Structure

The project follows a modular architecture to separate concerns and improve scalability:

```text
src/
├── modules/
│   ├── Auth/           # Authentication pages (Login, Register, ForgotPassword)
│   ├── Dashboard/      # Main overview dashboard
│   ├── Machines/       # Machine listing and details with charts
│   └── Reports/        # Production reports interface
├── shared/
│   ├── components/     # Reusable UI components (Layouts, Language Controls)
│   ├── contexts/       # Global state (Theme, Auth, Translations)
│   └── services/       # API configuration and Axios setup
└── App.jsx             # Main application entry point and routing