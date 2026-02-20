// Vite Entry Point
// This file acts as the primary build target for Vite.
// Currently it just imports the main CSS to ensure the bundler catches it,
// but it can be expanded into a React/Vue initialization point in the future.

import './References/smartadmin/css/smartadmin-production-plugins.min.css';
import './References/smartadmin/css/smartadmin-production.min.css';
import './References/smartadmin/css/smartadmin-skins.min.css';
import './References/jqwidgets/styles/jqx.base.css';
import './References/smartadmin/css/demo.css';
import './References/smartadmin/css/osy.css';

console.log("MUIO Frontend initialized via Vite bundler");
