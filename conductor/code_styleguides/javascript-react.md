# JavaScript/React Style Guide

## Standard
- ESLint with Airbnb config
- Prettier for formatting
- 2-space indentation

## Naming Conventions
- `camelCase` for variables, functions
- `PascalCase` for components, classes
- `UPPER_SNAKE_CASE` for constants

## React Components
```jsx
// Functional components with arrow functions
const LicenseCard = ({ license, onActivate }) => {
  return (
    <div className="license-card">
      <h3>{license.key}</h3>
      <button onClick={() => onActivate(license.id)}>
        Activate
      </button>
    </div>
  );
};

export default LicenseCard;
```

## Imports Order
```jsx
// React
import React, { useState, useEffect } from 'react';

// Third-party
import axios from 'axios';

// Components
import LicenseCard from './LicenseCard';

// Styles
import './Dashboard.css';
```

## Hooks
- Custom hooks: prefix with `use` (`useLicense`, `useAuth`)
- Keep hooks at top of component

## Props
- Destructure props in function signature
- Use PropTypes or TypeScript for type checking

## State Management
- Prefer local state when possible
- Use Context for shared state
- Redux for complex global state
