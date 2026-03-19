const fs = require('fs');
const { extractCurrentMilestone, escapeRegex, getRoadmapPhaseInternal } = require('./.agent/get-shit-done/bin/lib/core.cjs');
const cwd = process.cwd();
const roadmapPath = './.planning/ROADMAP.md';
const fileContent = fs.readFileSync(roadmapPath, 'utf-8');
const content = extractCurrentMilestone(fileContent, cwd);
console.log("EXTRACTED CONTENT LENGTH:", content.length);
console.log("CONTAINS PHASE 3:", content.includes('Phase 3'));

console.log("EXTRACTED CONTENT:", content.substring(0, 200) + '...');
const roadmapPhase = getRoadmapPhaseInternal(cwd, 3);
console.log("GET ROADMAP PHASE:", roadmapPhase);

const escapedPhase = escapeRegex('3');
const phasePattern = new RegExp(`#{2,4}\\s*Phase\\s+${escapedPhase}:\\s*([^\\n]+)`, 'i');
const headerMatch = content.match(phasePattern);
console.log("HEADER MATCH:", !!headerMatch);
