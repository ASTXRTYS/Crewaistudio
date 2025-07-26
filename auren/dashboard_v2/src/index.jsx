import { render } from 'solid-js/web';
import App from './App';
import './styles/main.css';

const root = document.getElementById('root');

// Clear loading message
root.innerHTML = '';

// Render the app
render(() => <App />, root); 