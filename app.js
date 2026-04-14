const state = {
  inning: 1,
  top: true,
  outs: 0,
  balls: 0,
  strikes: 0,
  awayRuns: Array(9).fill(0),
  homeRuns: Array(9).fill(0),
  bases: [false, false, false],
  gameOver: false,
};

const feed = document.getElementById('eventFeed');
const inningDisplay = document.getElementById('inningDisplay');
const countDisplay = document.getElementById('countDisplay');
const outsDisplay = document.getElementById('outsDisplay');
const inningsEl = document.getElementById('innings');
const zoneEl = document.getElementById('zone');
const ballEl = document.getElementById('ball');
const baseEls = [...document.querySelectorAll('.base')];

const fieldCard = document.getElementById('fieldCard');

fieldCard.addEventListener('mousemove', (event) => {
  const rect = fieldCard.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width - 0.5;
  const y = (event.clientY - rect.top) / rect.height - 0.5;
  const rotY = x * 8;
  const rotX = -y * 6;
  fieldCard.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
});

fieldCard.addEventListener('mouseleave', () => {
  fieldCard.style.transform = 'rotateX(0deg) rotateY(0deg)';
});

for (let i = 0; i < 9; i++) {
  const c = document.createElement('div');
  c.className = 'zone-cell';
  zoneEl.appendChild(c);
}

function total(runs) {
  return runs.reduce((a, b) => a + b, 0);
}

function renderInnings() {
  const headers = [...Array(9)].map((_, i) => i + 1).concat('R');
  inningsEl.innerHTML = '';
  headers.forEach((h, i) => {
    const head = document.createElement('div');
    head.className = 'cell head';
    head.textContent = h;
    inningsEl.appendChild(head);

    const away = document.createElement('div');
    away.className = 'cell';
    away.textContent = i < 9 && state.awayRuns[i] === 0 ? '-' : (i < 9 ? state.awayRuns[i] : total(state.awayRuns));
    inningsEl.appendChild(away);

    const home = document.createElement('div');
    home.className = 'cell';
    home.textContent = i < 9 && state.homeRuns[i] === 0 ? '-' : (i < 9 ? state.homeRuns[i] : total(state.homeRuns));
    inningsEl.appendChild(home);
  });
}

function renderHud() {
  inningDisplay.textContent = `${state.inning} ${state.top ? '▲' : '▼'}`;
  countDisplay.textContent = `${state.balls}-${state.strikes}`;
  outsDisplay.textContent = `${state.outs}`;
  baseEls.forEach((el) => {
    const b = Number(el.dataset.base) - 1;
    el.classList.toggle('active', state.bases[b]);
  });
}

function setFeed(text) {
  feed.textContent = text;
}

function animatePitch(target = Math.floor(Math.random() * 9)) {
  [...zoneEl.children].forEach((c, idx) => c.classList.toggle('pitch', idx === target));
  const coords = [
    [220, 150], [250, 150], [280, 150],
    [220, 200], [250, 200], [280, 200],
    [220, 250], [250, 250], [280, 250],
  ];
  const [x, y] = coords[target];
  ballEl.setAttribute('cx', String(x));
  ballEl.setAttribute('cy', String(y));
  setTimeout(() => {
    [...zoneEl.children].forEach((c) => c.classList.remove('pitch'));
    ballEl.setAttribute('cx', '250');
    ballEl.setAttribute('cy', '200');
  }, 280);
  return target;
}

function addRun(count = 1) {
  const idx = state.inning - 1;
  if (state.top) state.awayRuns[idx] += count;
  else state.homeRuns[idx] += count;
}

function advanceRunners(bases) {
  let scored = 0;
  for (let i = 2; i >= 0; i--) {
    if (state.bases[i]) {
      const next = i + bases;
      if (next >= 3) scored++;
      else state.bases[next] = true;
      state.bases[i] = false;
    }
  }
  if (bases >= 4) scored++;
  else state.bases[bases - 1] = true;
  if (scored) addRun(scored);
  return scored;
}

function nextHalfInning() {
  state.outs = 0;
  state.balls = 0;
  state.strikes = 0;
  state.bases = [false, false, false];
  if (!state.top) state.inning++;
  state.top = !state.top;

  if (state.inning > 9 && total(state.awayRuns) !== total(state.homeRuns)) {
    state.gameOver = true;
    const winner = total(state.awayRuns) > total(state.homeRuns) ? 'Sharks' : 'Falcons';
    setFeed(`Final: ${winner} win ${total(state.awayRuns)}-${total(state.homeRuns)}.`);
  }
}

function walk() {
  if (!state.bases[0]) state.bases[0] = true;
  else if (!state.bases[1]) state.bases[1] = true;
  else if (!state.bases[2]) state.bases[2] = true;
  else addRun(1);
  state.balls = 0;
  state.strikes = 0;
  setFeed('Ball four. Batter takes first.');
}

function strikeout(text = 'Strike three. Batter goes down swinging.') {
  state.outs++;
  state.balls = 0;
  state.strikes = 0;
  setFeed(text);
}

function pitch(action) {
  if (state.gameOver) return;

  const zone = animatePitch();
  const inZone = [1, 3, 4, 5, 7].includes(zone);
  const roll = Math.random();

  if (action === 'take') {
    if (inZone || roll > 0.84) {
      state.strikes++;
      setFeed('Called strike on the edge.');
    } else {
      state.balls++;
      setFeed('Ball misses outside.');
    }
  } else {
    const power = action === 'power';
    const whiffChance = power ? 0.33 : 0.23;
    const hitChance = power ? 0.34 : 0.42;

    if (roll < whiffChance) {
      state.strikes++;
      setFeed('Big cut and a miss.');
    } else if (roll < whiffChance + hitChance) {
      const hitRoll = Math.random();
      if (hitRoll > 0.96) {
        const scored = advanceRunners(4);
        setFeed(`CRUSHED! Home run${scored > 1 ? `, ${scored} runs score` : ''}.`);
      } else if (hitRoll > 0.82) {
        const s = advanceRunners(3);
        setFeed(`Triple to the gap! ${s ? `${s} run${s > 1 ? 's' : ''} score.` : ''}`);
      } else if (hitRoll > 0.58) {
        const s = advanceRunners(2);
        setFeed(`Lined double! ${s ? `${s} run${s > 1 ? 's' : ''} in.` : ''}`);
      } else {
        const s = advanceRunners(1);
        setFeed(`Sharp single. ${s ? `${s} run scores.` : 'Runners advance.'}`);
      }
      state.balls = 0;
      state.strikes = 0;
    } else {
      if (Math.random() > 0.55) {
        state.outs++;
        state.balls = 0;
        state.strikes = 0;
        setFeed('Routine fly ball. One away.');
      } else {
        state.strikes++;
        setFeed('Foul ball back into the screen.');
      }
    }
  }

  if (state.strikes >= 3) strikeout();
  if (state.balls >= 4) walk();
  if (state.outs >= 3) {
    setFeed(`Side retired. ${state.top ? 'Bottom' : 'Top'} of the ${state.inning}${state.top ? 'st' : 'th'} coming up.`);
    nextHalfInning();
  }

  renderHud();
  renderInnings();
}

function resetGame() {
  Object.assign(state, {
    inning: 1,
    top: true,
    outs: 0,
    balls: 0,
    strikes: 0,
    awayRuns: Array(9).fill(0),
    homeRuns: Array(9).fill(0),
    bases: [false, false, false],
    gameOver: false,
  });
  setFeed('New game loaded. Crowd is buzzing for first pitch.');
  renderHud();
  renderInnings();
}

document.getElementById('takeBtn').addEventListener('click', () => pitch('take'));
document.getElementById('swingBtn').addEventListener('click', () => pitch('swing'));
document.getElementById('powerBtn').addEventListener('click', () => pitch('power'));
document.getElementById('resetBtn').addEventListener('click', resetGame);

renderHud();
renderInnings();
