<template>
  <main class="app-shell">
    <header class="hero">
      <h1>PDF ➜ Anki</h1>
      <p>Transformez vos documents PDF en cartes mémoire prêtes à réviser.</p>
    </header>
    <section class="card">
      <PdfUploader />
    </section>
    <footer class="footer">
      <p>
        Déposez votre fichier PDF, générez un deck Anki et téléchargez le pour vos révisions.
      </p>
    </footer>
  </main>
</template>

<script setup>
import PdfUploader from './components/PdfUploader.vue'
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 2rem;
  padding: 3rem 1.5rem 4rem;
}

.hero {
  text-align: center;
}

.hero h1 {
  font-size: clamp(2.5rem, 4vw, 3.2rem);
  margin-bottom: 0.5rem;
  color: #1d4ed8;
}

.hero p {
  margin: 0;
  color: #475569;
  font-size: 1.125rem;
}

.card {
  width: min(680px, 100%);
  background: white;
  border-radius: 24px;
  padding: 2.5rem;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.12);
}

.footer {
  text-align: center;
  color: #64748b;
  max-width: 620px;
}
</style>
