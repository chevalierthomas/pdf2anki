<template>
  <form class="uploader" @submit.prevent="submit">
    <label class="dropzone" :class="{ 'dropzone--drag': isDragging }" @dragenter.prevent="onDrag(true)" @dragleave.prevent="onDrag(false)" @dragover.prevent @drop.prevent="handleDrop">
      <input ref="fileInput" type="file" accept="application/pdf" @change="handleFileChange" hidden />
      <div class="dropzone__content">
        <h2>Glissez un PDF ici ou cliquez pour sélectionner</h2>
        <p>Nous générerons automatiquement un deck Anki basé sur son contenu.</p>
        <button type="button" class="button-secondary" @click="pickFile">Choisir un fichier</button>
      </div>
    </label>

    <transition name="fade">
      <p v-if="fileName" class="file-name">Fichier sélectionné : {{ fileName }}</p>
    </transition>

    <transition name="fade">
      <div v-if="error" class="alert alert--error">{{ error }}</div>
    </transition>

    <transition name="fade">
      <div v-if="success" class="alert alert--success">
        Cartes générées ! Vérifiez la prévisualisation ci-dessous avant de télécharger le deck.
      </div>
    </transition>

    <transition name="fade">
      <section v-if="cards.length" class="preview">
        <header class="preview__header">
          <div>
            <h3>Prévisualisation des cartes</h3>
            <p>{{ cards.length }} carte<span v-if="cards.length > 1">s</span> générée<span v-if="cards.length > 1">s</span>.</p>
          </div>
          <a
            v-if="downloadUrl"
            class="button-primary preview__download"
            :href="downloadUrl"
            :download="downloadFilename"
          >
            Télécharger le deck Anki
          </a>
        </header>
        <ul class="preview__list">
          <li v-for="(card, index) in cards" :key="`${index}-${card.front}`" class="preview__card">
            <h4>Carte {{ index + 1 }}</h4>
            <p class="preview__label">Question</p>
            <p class="preview__content" v-html="card.front"></p>
            <p class="preview__label">Réponse</p>
            <p class="preview__content" v-html="card.back"></p>
          </li>
        </ul>
      </section>
    </transition>

    <button type="submit" class="button-primary" :disabled="isLoading">
      <span v-if="!isLoading">Générer le deck</span>
      <span v-else class="loader">
        <span class="loader__spinner" />
        Traitement en cours...
      </span>
    </button>
  </form>
</template>

<script setup>
import { ref } from 'vue'

const fileInput = ref(null)
const file = ref(null)
const fileName = ref('')
const error = ref('')
const success = ref(false)
const isLoading = ref(false)
const isDragging = ref(false)
const downloadUrl = ref('')
const downloadFilename = ref('deck.apkg')
const cards = ref([])

const resetFeedback = () => {
  error.value = ''
  success.value = false
  cards.value = []
  if (downloadUrl.value) {
    URL.revokeObjectURL(downloadUrl.value)
    downloadUrl.value = ''
  }
}

const pickFile = () => {
  fileInput.value?.click()
}

const handleFileChange = (event) => {
  resetFeedback()
  const [selected] = event.target.files
  if (!selected) {
    file.value = null
    fileName.value = ''
    return
  }
  if (selected.type !== 'application/pdf') {
    error.value = 'Seuls les fichiers PDF sont acceptés.'
    file.value = null
    fileName.value = ''
    return
  }
  file.value = selected
  fileName.value = selected.name
}

const handleDrop = (event) => {
  isDragging.value = false
  if (!event.dataTransfer?.files?.length) return
  const dropped = event.dataTransfer.files[0]
  if (dropped.type !== 'application/pdf') {
    error.value = 'Seuls les fichiers PDF sont acceptés.'
    return
  }
  file.value = dropped
  fileName.value = dropped.name
  resetFeedback()
}

const onDrag = (state) => {
  isDragging.value = state
}

const submit = async () => {
  resetFeedback()
  if (!file.value) {
    error.value = 'Merci de sélectionner un fichier PDF avant de lancer la génération.'
    return
  }
  isLoading.value = true

  try {
    const formData = new FormData()
    formData.append('pdf', file.value)

    const response = await fetch('/api/generate', {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}))
      throw new Error(payload.detail || 'La génération a échoué.')
    }

    const payload = await response.json()
    if (!payload?.deck_data || !Array.isArray(payload?.cards)) {
      throw new Error('Réponse inattendue du serveur.')
    }

    const binary = Uint8Array.from(atob(payload.deck_data), (char) => char.charCodeAt(0))
    const blob = new Blob([binary], { type: 'application/apkg' })

    downloadUrl.value = URL.createObjectURL(blob)
    downloadFilename.value = payload.deck_filename || 'deck.apkg'
    const sanitizedCards = payload.cards.map((card) => ({
      front: String(card?.front ?? ''),
      back: String(card?.back ?? '')
    }))

    cards.value = sanitizedCards
    success.value = true
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.uploader {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.dropzone {
  border: 2px dashed #cbd5f5;
  border-radius: 18px;
  padding: 2.5rem;
  background: rgba(229, 231, 235, 0.4);
  transition: border-color 0.3s, background 0.3s;
  cursor: pointer;
}

.dropzone--drag {
  border-color: #1d4ed8;
  background: rgba(59, 130, 246, 0.15);
}

.dropzone__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 0.75rem;
}

.dropzone h2 {
  margin: 0;
  font-size: 1.4rem;
  color: #1f2937;
}

.dropzone p {
  margin: 0;
  color: #4b5563;
}

.button-primary,
.button-secondary {
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.button-primary { 
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: white;
  box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35);
}

.preview {
  border: 1px solid rgba(37, 99, 235, 0.15);
  border-radius: 16px;
  padding: 1.5rem;
  background: rgba(219, 234, 254, 0.35);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.preview__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.preview__header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.preview__header p {
  margin: 0.25rem 0 0;
  color: #374151;
}

.preview__download {
  text-decoration: none;
  white-space: nowrap;
}

.preview__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 1rem;
}

.preview__card {
  background: white;
  border-radius: 14px;
  padding: 1.25rem;
  box-shadow: 0 12px 30px rgba(37, 99, 235, 0.12);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.preview__card h4 {
  margin: 0;
  color: #1d4ed8;
  font-size: 1rem;
}

.preview__label {
  margin: 0;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
}

.preview__content {
  margin: 0;
  color: #111827;
  background: rgba(59, 130, 246, 0.08);
  border-radius: 10px;
  padding: 0.75rem;
  line-height: 1.4;
  word-break: break-word;
}

.preview__content :deep(br) {
  content: '';
}

.button-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.button-secondary {
  background: white;
  color: #1d4ed8;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.18);
}

.button-primary:not(:disabled):hover,
.button-secondary:hover {
  transform: translateY(-2px);
}

.file-name {
  margin: 0;
  color: #334155;
  font-weight: 600;
}

.alert {
  padding: 1rem 1.2rem;
  border-radius: 14px;
  font-weight: 500;
}

.alert--error {
  background: rgba(248, 113, 113, 0.15);
  color: #b91c1c;
}

.alert--success {
  background: rgba(34, 197, 94, 0.15);
  color: #15803d;
}

.alert a {
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
}

.loader {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.loader__spinner {
  width: 1.1rem;
  height: 1.1rem;
  border: 3px solid rgba(255, 255, 255, 0.6);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
