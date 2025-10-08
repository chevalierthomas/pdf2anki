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
        Deck généré ! <a :href="downloadUrl" download>Cliquer ici pour télécharger</a>.
      </div>
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

const resetFeedback = () => {
  error.value = ''
  success.value = false
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

    const blob = await response.blob()
    downloadUrl.value = URL.createObjectURL(blob)
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
