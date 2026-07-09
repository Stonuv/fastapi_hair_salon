<template>
  <div ref="containerEl" class="absolute inset-0 overflow-hidden">
    <canvas ref="canvasEl" class="absolute inset-0 h-full w-full" />
    <div v-if="!ready" class="absolute inset-0 animate-pulse bg-black/5" aria-hidden="true" />
  </div>
</template>

<script setup>
/**
 * Интерактивная 3D-модель зала барбершопа для главного экрана.
 * Модель вращается по Y/X вслед за курсором (см. onPointerMove) —
 * камера и свет фиксированы, крутится сама сцена. Загружается лениво
 * (IntersectionObserver) — исходный .glb весит ~13MB и не сжат Draco,
 * несмотря на имя файла (в manifest нет KHR_draco_mesh_compression).
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'

const MODEL_URL = '/models/salon-room.glb'
// Общий размах поворота по курсору держим в районе 20-30°: основной
// довесок — по Y (лево/право), лёгкий наклон по X (верх/низ) сверху.
const Y_RANGE = THREE.MathUtils.degToRad(26)
const X_RANGE = THREE.MathUtils.degToRad(10)
const DAMPING = 0.07

const containerEl = ref(null)
const canvasEl = ref(null)
const ready = ref(false)

let renderer = null
let scene = null
let camera = null
let model = null
let pmremGenerator = null
let resizeObserver = null
let intersectionObserver = null
let rafId = null
let visible = false
let loadStarted = false
const targetRotation = { x: 0, y: 0 }
const currentRotation = { x: 0, y: 0 }

function onPointerMove(event) {
  const el = containerEl.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) return
  const nx = THREE.MathUtils.clamp((event.clientX - rect.left) / rect.width, 0, 1)
  const ny = THREE.MathUtils.clamp((event.clientY - rect.top) / rect.height, 0, 1)
  targetRotation.y = (nx - 0.5) * Y_RANGE
  targetRotation.x = (ny - 0.5) * X_RANGE
}

function initScene() {
  scene = new THREE.Scene()

  camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100)
  camera.position.set(3.6, 2.9, 3.9)
  camera.lookAt(0, 0.15, 0)

  renderer = new THREE.WebGLRenderer({ canvas: canvasEl.value, antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05

  // Модель использует стеклянные/прозрачные материалы (KHR_materials_transmission) —
  // без environment-карты они выглядят плоско-серыми. RoomEnvironment собирает
  // нейтральную студийную карту прямо в браузере, без внешних .hdr файлов.
  pmremGenerator = new THREE.PMREMGenerator(renderer)
  scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture

  scene.add(new THREE.HemisphereLight(0xfff3e0, 0x201a14, 0.9))
  const key = new THREE.DirectionalLight(0xffffff, 1.4)
  key.position.set(5, 6, 4)
  scene.add(key)

  resize()
}

function resize() {
  if (!containerEl.value || !renderer) return
  const { clientWidth: w, clientHeight: h } = containerEl.value
  if (w === 0 || h === 0) return
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h, false)
}

// Некоторые экспортированные из Blender сцены тащат за собой гигантский
// плоский ground-catcher плейн (на пару порядков больше самой комнаты) —
// он не виден на референсных рендерах, но ломает автоматическое
// масштабирование по общему bounding box. Отсекаем такие мешы по резкому
// разрыву в размере (не по имени — оно не гарантировано между экспортами).
function removeOutlierMeshes(root) {
  const entries = []
  root.traverse((obj) => {
    if (obj.isMesh) {
      const size = new THREE.Box3().setFromObject(obj).getSize(new THREE.Vector3())
      entries.push({ obj, diagonal: size.length() })
    }
  })
  entries.sort((a, b) => b.diagonal - a.diagonal)
  let i = 0
  while (i < entries.length - 1 && entries.length - i > 1 && entries[i].diagonal > entries[i + 1].diagonal * 5) {
    // Полностью убираем из графа сцены, а не просто visible = false —
    // Box3.setFromObject() игнорирует .visible и всё равно учтёт узел.
    entries[i].obj.removeFromParent()
    i += 1
  }
}

function loadModel() {
  loadStarted = true
  new GLTFLoader().load(
    MODEL_URL,
    (gltf) => {
      model = gltf.scene
      removeOutlierMeshes(model)
      const box = new THREE.Box3().setFromObject(model)
      const size = box.getSize(new THREE.Vector3())
      const center = box.getCenter(new THREE.Vector3())
      const maxDim = Math.max(size.x, size.y, size.z) || 1
      const scale = 4.0 / maxDim
      model.scale.setScalar(scale)
      model.position.set(-center.x * scale, -center.y * scale, -center.z * scale)
      scene.add(model)
      ready.value = true
      startLoop()
    },
    undefined,
    (err) => {
      console.error('Не удалось загрузить 3D-модель зала', err)
    },
  )
}

function animate() {
  rafId = requestAnimationFrame(animate)
  currentRotation.x += (targetRotation.x - currentRotation.x) * DAMPING
  currentRotation.y += (targetRotation.y - currentRotation.y) * DAMPING
  if (model) {
    model.rotation.x = currentRotation.x
    model.rotation.y = currentRotation.y
  }
  renderer.render(scene, camera)
}

function startLoop() {
  if (rafId === null && visible && model) animate()
}

function stopLoop() {
  if (rafId !== null) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
}

function disposeMaterial(material) {
  if (!material) return
  Object.values(material).forEach((value) => {
    if (value?.isTexture) value.dispose()
  })
  material.dispose()
}

onMounted(() => {
  initScene()

  intersectionObserver = new IntersectionObserver(
    ([entry]) => {
      visible = entry.isIntersecting
      if (visible) {
        if (!loadStarted) loadModel()
        else startLoop()
      } else {
        stopLoop()
      }
    },
    { rootMargin: '200px' },
  )
  intersectionObserver.observe(containerEl.value)

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(containerEl.value)

  window.addEventListener('pointermove', onPointerMove, { passive: true })
})

onBeforeUnmount(() => {
  stopLoop()
  window.removeEventListener('pointermove', onPointerMove)
  intersectionObserver?.disconnect()
  resizeObserver?.disconnect()
  pmremGenerator?.dispose()
  model?.traverse((obj) => {
    obj.geometry?.dispose()
    const materials = Array.isArray(obj.material) ? obj.material : [obj.material]
    materials.forEach(disposeMaterial)
  })
  renderer?.dispose()
})
</script>
