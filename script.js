(() => {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ambient = document.querySelector('.ambient');
  const cursor = document.querySelector('.cursor-heart');

  if (!reducedMotion && ambient) {
    const symbols = ['♥', '♡', '✿', '❀'];
    const addParticle = () => {
      const particle = document.createElement('span');
      const isPetal = Math.random() > 0.66;
      particle.className = `particle${isPetal ? ' particle--petal' : ''}`;
      particle.textContent = symbols[Math.floor(Math.random() * symbols.length)];
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.fontSize = `${9 + Math.random() * 15}px`;
      particle.style.setProperty('--drift', `${Math.round(Math.random() * 150 - 75)}px`);
      particle.style.setProperty('--spin', `${Math.round(Math.random() * 460 - 230)}deg`);
      particle.style.animationDuration = `${9 + Math.random() * 9}s`;
      ambient.append(particle);
      window.setTimeout(() => particle.remove(), 19000);
    };
    for (let index = 0; index < 11; index += 1) window.setTimeout(addParticle, index * 280);
    window.setInterval(addParticle, 1150);
  }

  if (cursor && window.matchMedia('(hover: hover) and (pointer: fine)').matches && !reducedMotion) {
    window.addEventListener('pointermove', (event) => {
      cursor.style.left = `${event.clientX}px`;
      cursor.style.top = `${event.clientY}px`;
      cursor.classList.add('is-visible');
    }, { passive: true });
    document.addEventListener('pointerleave', () => cursor.classList.remove('is-visible'));
  }

  const dodgeMessages = new WeakMap();
  document.querySelectorAll('[data-dodge]').forEach((button) => {
    const stage = button.closest('[data-dodge-stage]');
    const message = button.closest('.no-choice-column')?.querySelector('[data-dodge-message]');
    const messages = (button.dataset.messages || '').split('|').filter(Boolean);
    let messageIndex = 0;
    let moveCount = 0;
    dodgeMessages.set(button, () => {
      if (!stage) return;
      const stageBounds = stage.getBoundingClientRect();
      const buttonBounds = button.getBoundingClientRect();
      const maxX = Math.max(0, stageBounds.width - buttonBounds.width);
      const maxY = Math.max(0, stageBounds.height - buttonBounds.height);
      const angle = Math.random() * Math.PI * 2;
      const distance = Math.min(26 + moveCount * 5, Math.max(10, maxX * .44));
      const currentX = button.offsetLeft || (stage.clientWidth - button.offsetWidth) / 2;
      const currentY = button.offsetTop || (stage.clientHeight - button.offsetHeight) / 2;
      let nextX = currentX + Math.cos(angle) * distance;
      let nextY = currentY + Math.sin(angle) * Math.min(distance, maxY / 2);
      if (maxX < 1) nextX = 0;
      else nextX = Math.max(0, Math.min(maxX, nextX));
      if (maxY < 1) nextY = 0;
      else nextY = Math.max(0, Math.min(maxY, nextY));
      button.classList.add('is-dodging');
      button.style.left = `${nextX}px`;
      button.style.top = `${nextY}px`;
      moveCount += 1;
      if (message && messages.length) {
        message.textContent = messages[messageIndex % messages.length];
        messageIndex += 1;
      }
    });
    button.addEventListener('pointerenter', (event) => {
      if (event.pointerType === 'mouse') dodgeMessages.get(button)();
    });
    button.addEventListener('pointerdown', (event) => {
      if (event.pointerType === 'touch') dodgeMessages.get(button)();
    });
    button.addEventListener('click', (event) => {
      if (event.detail === 0) {
        const declineForm = document.querySelector('form.honest-answer');
        declineForm?.requestSubmit();
      }
    });
  });

  const celebrate = () => {
    if (reducedMotion) return;
    const layer = document.createElement('div');
    layer.className = 'celebration';
    layer.setAttribute('aria-hidden', 'true');
    const colors = ['#e34f7b', '#ffc05e', '#f48eae', '#fff4f7', '#b97bd0'];
    for (let index = 0; index < 52; index += 1) {
      const piece = document.createElement('span');
      const isHeart = index < 18;
      piece.className = isHeart ? 'celebration-heart' : 'confetti';
      if (isHeart) {
        piece.textContent = index % 2 ? '♥' : '♡';
        piece.style.setProperty('--size', `${14 + Math.random() * 23}px`);
      } else {
        piece.style.setProperty('--color', colors[Math.floor(Math.random() * colors.length)]);
      }
      const angle = Math.random() * Math.PI * 2;
      const distance = 100 + Math.random() * Math.max(window.innerWidth, window.innerHeight) * .58;
      piece.style.setProperty('--x', `${Math.cos(angle) * distance}px`);
      piece.style.setProperty('--y', `${Math.sin(angle) * distance}px`);
      piece.style.setProperty('--rotation', `${Math.round(Math.random() * 900 - 450)}deg`);
      layer.append(piece);
    }
    document.body.append(layer);
    window.setTimeout(() => layer.remove(), 1350);
  };

  document.querySelectorAll('form[data-celebrate-form], form[data-transition-submit]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (form.dataset.submitting) return;
      event.preventDefault();
      form.dataset.submitting = 'true';
      celebrate();
      const delay = reducedMotion ? 0 : 720;
      window.setTimeout(() => form.submit(), delay);
    });
  });

  document.querySelectorAll('a[data-transition]').forEach((link) => {
    link.addEventListener('click', (event) => {
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      document.body.classList.add('is-leaving');
      window.setTimeout(() => { window.location.href = link.href; }, reducedMotion ? 0 : 220);
    });
  });

  const randomMessage = (messages, previous = '') => {
    if (messages.length < 2) return messages[0] || '';
    const options = messages.filter((message) => message !== previous);
    return options[Math.floor(Math.random() * options.length)];
  };

  const funnyMessages = {
    joke: [
      "Aashi, you officially have a lifetime subscription to Jahid's nonsense! 😂❤️",
      "Booboo Baby, your boyfriend's brain is 50% love and 50% loading... 🤣",
      "Aashi, congratulations! You have unlocked unlimited bad jokes from Jahid. 😂",
    ],
    roast: [
      "Breaking news: Aashiyana has stolen Jahid's heart, and no refunds are available! 💘",
      "Relationship status: Aashi is the boss, and Jahid is the unpaid employee. 😂",
      "My Aashi is cute, but her ability to irritate Jahid is legendary! 🤣❤️",
    ],
    love: [
      "Warning: Jahid may randomly ask for attention, hugs, and cute replies! 🙈",
      "A little extra love, delivered directly to my Booboo Baby. 💗",
    ],
    cute: [
      "Too late, Aashi. The cute has already been noticed and documented. 🙈",
      "Stop being so cute? My Qalbi, I fear that ship has sailed. 😂❤️",
    ],
    surprise: [
      "Surprise: Jahid has one more little love letter waiting just for you. 🎁💌",
      "Your next surprise is one button away, my Aashi. 🌙❤️",
    ],
  };
  const funnyIndexes = new Map();
  const funnyDisplay = document.querySelector('[data-funny-message]');
  const funnyResponse = document.querySelector('[data-funny-response]');
  document.querySelectorAll('[data-funny-action]').forEach((button) => {
    button.addEventListener('click', () => {
      const action = button.dataset.funnyAction;
      const messages = funnyMessages[action] || [];
      const last = funnyIndexes.get(action) ?? (action === 'joke' ? 0 : -1);
      const index = messages.length ? (last + 1) % messages.length : 0;
      funnyIndexes.set(action, index);
      const message = messages[index] || '';
      if (funnyDisplay) funnyDisplay.textContent = message;
      if (funnyResponse) {
        funnyResponse.textContent = action === 'love'
          ? 'A little more love for my Booboo Baby!'
          : action === 'surprise'
            ? 'Ready for the last little surprise? 💌'
            : action === 'cute'
              ? 'Officially too cute. Case closed. 💗'
              : 'The relationship committee has reviewed this joke. 😂';
      }
      if (action === 'love') celebrate();
      if (action === 'surprise' && !reducedMotion) button.classList.add('is-sparkling');
    });
  });

  const finalMessages = {
    miss: [
      "Obviously! I'm unforgettable. 🤣",
      "Aashi, don't lie. Your smile already answered! ❤️",
      "Jahid's confidence level: 1000%. Accuracy: still loading... 😂",
    ],
    jokes: [
      "Booboo Baby, your boyfriend's brain is 50% love and 50% loading... 🤣",
      "Relationship status: Aashi is the boss, and Jahid is the unpaid employee. 😂",
      "Aashi, you officially have a lifetime subscription to Jahid's nonsense! 😂❤️",
      "Warning: Jahid may randomly ask for attention, hugs, and cute replies! 🙈",
      "Breaking news: Aashiyana has stolen Jahid's heart, and no refunds are available! 💘",
      "My Aashi is cute, but her ability to irritate Jahid is legendary! 🤣❤️",
    ],
    love: ["A little more love for my Booboo Baby!"],
    secret: ["You found the secret! Jahid owes Aashi one extra-special date. ❤️"],
  };
  let lastFinalMessage = '';
  document.querySelectorAll('[data-final-action]').forEach((button) => {
    button.addEventListener('click', () => {
      const messages = finalMessages[button.dataset.finalAction] || [];
      lastFinalMessage = randomMessage(messages, lastFinalMessage);
      const output = document.querySelector('[data-final-response]');
      if (output) output.textContent = lastFinalMessage;
      if (button.dataset.finalAction === 'love') celebrate();
    });
  });

  const editingMessages = {
    rewatches: [
      'Only 47 times? Rookie numbers! 😂',
      'The editor and the audience are the same person. 🤣',
      'Aashi checking her own edit again... breaking news! 💀',
    ],
    skills: [
      "Jahid's editing skills: Under review. His talent for loving Aashi: 100/10. ❤️😂",
    ],
    fan: [
      'Correct answer: Jahid. No other answer will be accepted by this extremely unbiased website. 🤣❤️',
    ],
    quiet: [
      "Okay, Aashi... I'll be quiet for exactly 3 seconds. 1... 2... 3... BABYYYY! 😂❤️",
    ],
    compliment: [
      'Your transitions are smooth, your creativity is amazing, and your biggest fan is even more dramatic than your edits. 😂🌹',
    ],
    surprise: [
      'My Aashi, behind every joke is a Jahid who is genuinely proud of you. Keep chasing your dreams, my Qalbi. ❤️',
    ],
  };
  const lastEditingMessages = new Map();
  document.querySelectorAll('[data-editing-action]').forEach((button) => {
    button.addEventListener('click', () => {
      const action = button.dataset.editingAction;
      const message = randomMessage(editingMessages[action] || [], lastEditingMessages.get(action));
      lastEditingMessages.set(action, message);
      const response = document.querySelector('[data-editing-response]');
      if (response) {
        response.textContent = message;
        response.classList.remove('is-visible');
        requestAnimationFrame(() => response.classList.add('is-visible'));
      }
      if (action === 'surprise') celebrate();
    });
  });

  const typingSource = document.querySelector('[data-typing-source]');
  const typingTarget = document.querySelector('[data-typing]');
  if (typingSource && typingTarget) {
    const fullMessage = typingSource.textContent.trim();
    typingTarget.setAttribute('aria-label', fullMessage);
    if (reducedMotion) {
      typingTarget.textContent = fullMessage;
    } else {
      let characterIndex = 0;
      const typeNext = () => {
        characterIndex = Math.min(characterIndex + 3, fullMessage.length);
        typingTarget.textContent = fullMessage.slice(0, characterIndex);
        if (characterIndex < fullMessage.length) window.setTimeout(typeNext, 22);
      };
      typeNext();
    }
  }

  const surpriseVideo = document.querySelector('[data-surprise-video]');
  const videoError = document.querySelector('[data-video-error]');
  surpriseVideo?.addEventListener('error', () => {
    if (videoError) videoError.hidden = false;
  });
  surpriseVideo?.addEventListener('loadedmetadata', () => {
    if (videoError) videoError.hidden = true;
  });
})();
