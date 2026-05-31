(() => {
  const workspace = document.querySelector(".workspace");
  if (!workspace) return;

  const cardsDataElement = document.getElementById("cards-data");
  const cardsData = cardsDataElement ? JSON.parse(cardsDataElement.textContent) : [];
  const cardsById = new Map(cardsData.map((card) => [card.id, card]));
  let generatedCards = [];

  const csrfToken = () => {
    const input = document.querySelector("input[name='csrfmiddlewaretoken']");
    return input ? input.value : "";
  };

  const openModal = (id) => {
    const modal = document.getElementById(id);
    if (modal) modal.hidden = false;
  };

  const closeModal = (modal) => {
    modal.hidden = true;
  };

  document.querySelectorAll("[data-open-modal]").forEach((button) => {
    button.addEventListener("click", () => openModal(button.dataset.openModal));
  });

  document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", () => {
      const modal = button.closest(".modal");
      if (modal) closeModal(modal);
    });
  });

  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal(modal);
    });
  });

  document.querySelectorAll("[data-edit-card]").forEach((button) => {
    button.addEventListener("click", () => {
      const card = cardsById.get(button.dataset.editCard);
      const form = document.getElementById("edit-card-form");
      if (!card || !form) return;
      form.action = card.update_url;
      form.elements.front.value = card.front;
      form.elements.back.value = card.back;
      form.elements.difficulty.value = card.difficulty || "";
      form.elements.tags.value = card.tags || "";
      form.elements.example_sentence.value = card.example_sentence || "";
      form.elements.pronunciation.value = card.pronunciation || "";
      openModal("edit-card-modal");
    });
  });

  document.querySelectorAll("[data-delete-card]").forEach((button) => {
    button.addEventListener("click", () => {
      const card = cardsById.get(button.dataset.deleteCard);
      const form = document.getElementById("delete-card-form");
      if (!card || !form) return;
      form.action = card.delete_url;
      openModal("delete-card-modal");
    });
  });

  const aiForm = document.getElementById("ai-generate-form");
  const loading = document.getElementById("ai-loading");
  const preview = document.getElementById("ai-preview");
  const previewList = document.getElementById("ai-preview-list");
  const previewTitle = document.getElementById("ai-preview-title");
  const saveButton = document.getElementById("save-ai-cards");

  const setLoading = (isLoading) => {
    if (loading) loading.hidden = !isLoading;
    if (aiForm) {
      aiForm.querySelectorAll("input, select, button").forEach((field) => {
        field.disabled = isLoading;
      });
    }
  };

  const showNotice = (message, isError = false) => {
    const container = document.querySelector(".messages") || document.createElement("div");
    if (!container.classList.contains("messages")) {
      container.className = "messages";
      document.querySelector(".main").prepend(container);
    }
    const notice = document.createElement("div");
    notice.className = `message ${isError ? "error" : "success"}`;
    notice.textContent = message;
    container.appendChild(notice);
    window.setTimeout(() => notice.remove(), 5200);
  };

  aiForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const generateUrl = workspace.dataset.aiGenerateUrl;
    if (!generateUrl) return;
    setLoading(true);
    if (preview) preview.hidden = true;
    try {
      const response = await fetch(generateUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken() },
        body: new FormData(aiForm),
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.message || "AI generation failed.");
      }
      generatedCards = data.cards || [];
      renderPreview();
    } catch (error) {
      showNotice(error.message, true);
    } finally {
      setLoading(false);
    }
  });

  const renderPreview = () => {
    if (!previewList || !preview) return;
    previewList.innerHTML = "";
    previewTitle.textContent = `${generatedCards.length} generated cards`;
    generatedCards.forEach((card, index) => {
      const back = card.back || {};
      const pronunciation = back.pronunciation || {};
      const examples = Array.isArray(back.examples) && back.examples.length ? back.examples : [{ text: "" }];
      const item = document.createElement("article");
      item.className = "preview-card";
      item.dataset.index = String(index);
      item.innerHTML = `
        <div class="preview-head">
          <label><input type="checkbox" data-field="selected" checked> Keep</label>
          <label><span>Front</span><input data-field="front" value="${escapeAttr(card.front || "")}"></label>
          <label><span>Difficulty</span>
            <select data-field="difficulty">
              <option value="easy" ${card.difficulty === "easy" ? "selected" : ""}>Easy</option>
              <option value="medium" ${!card.difficulty || card.difficulty === "medium" ? "selected" : ""}>Medium</option>
              <option value="hard" ${card.difficulty === "hard" ? "selected" : ""}>Hard</option>
            </select>
          </label>
          <button class="icon-button danger" type="button" data-remove-preview aria-label="Remove preview card">
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="M6 7l1 13h10l1-13"/><path d="M9 7V4h6v3"/></svg>
          </button>
        </div>
        <label><span>Definition</span><textarea rows="3" data-field="definition">${escapeHtml(back.definition || "")}</textarea></label>
        <div class="form-grid">
          <label><span>Pronunciation</span><input data-field="pronunciation" value="${escapeAttr(pronunciation.text || "")}"></label>
          <label><span>Part of speech</span><input data-field="part_of_speech" value="${escapeAttr(back.part_of_speech || "")}"></label>
        </div>
        <label><span>Usage</span><textarea rows="2" data-field="usage">${escapeHtml(back.usage || "")}</textarea></label>
        <label><span>Memory tip</span><input data-field="memory_tip" value="${escapeAttr(back.memory_tip || "")}"></label>
        <div class="preview-examples">
          <span class="eyebrow">Examples</span>
          ${examples.map((example) => `<textarea rows="2" data-field="example">${escapeHtml(example.text || "")}</textarea>`).join("")}
        </div>
      `;
      previewList.appendChild(item);
    });
    preview.hidden = false;
  };

  previewList?.addEventListener("click", (event) => {
    const remove = event.target.closest("[data-remove-preview]");
    if (!remove) return;
    const card = remove.closest(".preview-card");
    generatedCards.splice(Number(card.dataset.index), 1);
    renderPreview();
  });

  saveButton?.addEventListener("click", async () => {
    const saveUrl = workspace.dataset.aiSaveUrl;
    if (!saveUrl) return;
    const cards = collectPreviewCards();
    if (!cards.some((card) => card.selected)) {
      showNotice("Select at least one generated card.", true);
      return;
    }
    saveButton.disabled = true;
    try {
      const response = await fetch(saveUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken(),
        },
        body: JSON.stringify({ cards }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.message || "Could not save generated cards.");
      }
      showNotice(`${data.created} cards saved to this deck.`);
      window.setTimeout(() => window.location.reload(), 800);
    } catch (error) {
      showNotice(error.message, true);
    } finally {
      saveButton.disabled = false;
    }
  });

  const collectPreviewCards = () => {
    return [...document.querySelectorAll(".preview-card")].map((item) => {
      const examples = [...item.querySelectorAll("[data-field='example']")]
        .map((input) => ({ text: input.value.trim(), tts: null }))
        .filter((example) => example.text);
      return {
        selected: item.querySelector("[data-field='selected']").checked,
        front: item.querySelector("[data-field='front']").value.trim(),
        difficulty: item.querySelector("[data-field='difficulty']").value,
        back: {
          definition: item.querySelector("[data-field='definition']").value.trim(),
          pronunciation: {
            text: item.querySelector("[data-field='pronunciation']").value.trim(),
            hint: null,
            tts: null,
          },
          part_of_speech: item.querySelector("[data-field='part_of_speech']").value.trim(),
          usage: item.querySelector("[data-field='usage']").value.trim(),
          examples,
          memory_tip: item.querySelector("[data-field='memory_tip']").value.trim(),
        },
      };
    });
  };

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll('"', "&quot;");
  }
})();
