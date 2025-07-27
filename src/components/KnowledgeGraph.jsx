import { createSignal, onMount, onCleanup } from 'solid-js';
import * as d3 from 'd3';

export function KnowledgeGraph() {
    // ... existing code ...

    d3.select(canvas).call(zoom);
 
    // Particles.js will be added in a future update after proper installation
    
    // Handle resize
    // ... existing code ... 