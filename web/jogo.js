/* Colônia — Web Demo
 *
 * Tradução para o navegador da Placa de Cultura do Projeto 018 (Python + tkinter).
 * Cada parte diz de qual arquivo .py ela veio, para dar para comparar lado a lado.
 *
 * O jogo de PC continua sendo a versão completa. Aqui só tem a placa:
 * a meta da demo é chegar à Bactéria Ápice (estágio 10).
 */
"use strict";

// ============================================================
// evolucao_dados.py — os estágios
// ============================================================
const ESTAGIOS = [
  ["Cianobactéria Primitiva", 1], ["Micrococo Simples", 2], ["Bacilo Jovem", 3],
  ["Espirilo Ativo", 4], ["Estreptococo Duplo", 5], ["Estafilococo Robusto", 6],
  ["Bacilo Resiliente", 7], ["Cianobactéria Madura", 8], ["Colônia Bacteriana", 9],
  ["Bactéria Ápice", 10],
  ["Partícula Viral", 11], ["Capsídeo Simples", 12], ["Vírus Icosaédrico", 14],
  ["Bacteriófago Jovem", 15], ["Vírus Envelopado", 16], ["Vírus Mutante", 17],
  ["Vírus Agressivo", 18], ["Vírus Dominante", 19], ["Vírus Ápice", 20],
  ["Célula Primordial", 21], ["Célula Nucleada", 22], ["Célula Especializada", 23],
  ["Célula Colonial", 24], ["Célula Adaptada", 25], ["Forma de Vida Suprema", 30],
];
const TOTAL_ESTAGIOS = ESTAGIOS.length;
const BLOCOS = [
  { nome: "Bactérias", inicio: 1, fim: 10, emoji: "🦠" },
  { nome: "Vírus", inicio: 11, fim: 19, emoji: "✴️" },
  { nome: "Células Complexas", inicio: 20, fim: 25, emoji: "🧫" },
];
const TAMANHO_PRIMEIRO_ESTAGIO = 5;
const TAMANHO_ULTIMO_ESTAGIO = 63;

const ESTAGIO_FINAL_DA_DEMO = 10;   // Bactéria Ápice: fim do bloco das Bactérias

function nomeDoEstagio(estagio) { return ESTAGIOS[estagio - 1][0]; }

function blocoDoEstagio(estagio) {
  return BLOCOS.find(b => b.inicio <= estagio && estagio <= b.fim) || BLOCOS[BLOCOS.length - 1];
}

function tamanhoDoEstagio(estagio) {
  const passo = (TAMANHO_ULTIMO_ESTAGIO - TAMANHO_PRIMEIRO_ESTAGIO) / (TOTAL_ESTAGIOS - 1);
  return Math.round((TAMANHO_PRIMEIRO_ESTAGIO + (estagio - 1) * passo) * 10) / 10;
}

// cor dos pontinhos do minimapa (mesma conta do Python, com HSV)
function hsvParaHex(h, s, v) {
  const i = Math.floor(h * 6), f = h * 6 - i;
  const p = v * (1 - s), q = v * (1 - f * s), t = v * (1 - (1 - f) * s);
  const [r, g, b] = [[v, t, p], [q, v, p], [p, v, t], [p, q, v], [t, p, v], [v, p, q]][i % 6];
  return "#" + [r, g, b].map(c => Math.floor(c * 255).toString(16).padStart(2, "0")).join("");
}

const _coresDosEstagios = {};
function corDoEstagio(estagio) {
  if (_coresDosEstagios[estagio]) return _coresDosEstagios[estagio];
  const bloco = blocoDoEstagio(estagio);
  const posicao = (estagio - bloco.inicio) / Math.max(1, bloco.fim - bloco.inicio);
  let matiz;
  if (bloco.nome === "Bactérias") matiz = 10 + posicao * 30;
  else if (bloco.nome === "Vírus") matiz = 260 - posicao * 40;
  else matiz = 95 - posicao * 45;
  const cor = hsvParaHex(matiz / 360, Math.min(0.55 + posicao * 0.35, 0.95), Math.min(0.65 + posicao * 0.3, 0.95));
  _coresDosEstagios[estagio] = cor;
  return cor;
}

// ============================================================
// comportamento.py — só os 3 naturais e o Infectado (as IAs são da versão completa)
// ============================================================
const COMPORTAMENTOS = {
  "Calmo": {
    emoji: "😌", velocidadeMult: 0.6, tamanhoMult: 1.0, movimento: "suave", natural: true,
    descricao: "Lento, faz curvas suaves e às vezes para um pouco.",
  },
  "Agitado": {
    emoji: "⚡", velocidadeMult: 1.6, tamanhoMult: 0.9, movimento: "reto", natural: true,
    descricao: "Rápido e um pouco menor. Anda em linha reta e quica nas bordas, então encontra parceiros antes.",
  },
  "Irritado": {
    emoji: "😠", velocidadeMult: 1.2, tamanhoMult: 1.0, movimento: "persegue", natural: true,
    descricao: "Vai atrás do vizinho mais próximo e empurra os outros.",
  },
  "Infectado": {
    emoji: "☣️", velocidadeMult: 0.8, tamanhoMult: 1.0, movimento: "zigue", natural: false,
    chanceContagio: 0.25,
    descricao: "Só surge quando o cientista usa 'Infectar'. Anda em zigue-zague e pode passar a infecção para quem encostar nele.",
  },
};
const LISTA_NATURAIS = Object.keys(COMPORTAMENTOS).filter(nome => COMPORTAMENTOS[nome].natural);

function sortear(lista) { return lista[Math.floor(Math.random() * lista.length)]; }
function aleatorio(minimo, maximo) { return minimo + Math.random() * (maximo - minimo); }
function inteiroAleatorio(minimo, maximo) { return Math.floor(aleatorio(minimo, maximo + 1)); }
function limitar(valor, minimo, maximo) { return Math.max(minimo, Math.min(maximo, valor)); }

function modificadores(comportamento) { return COMPORTAMENTOS[comportamento] || COMPORTAMENTOS["Calmo"]; }

function herdarComportamento(pai1, pai2) {
  if (pai1 === pai2) return pai1;
  if (pai1 === "Infectado" || pai2 === "Infectado") return "Infectado";   // a infecção passa para o filho
  return sortear([pai1, pai2]);
}

// ============================================================
// habilidades.py
// ============================================================
const VELOCIDADE_MIN = 0.5, VELOCIDADE_MAX = 2.5;

function gerarHabilidadesIniciais(comportamento) {
  return {
    velocidadeMod: Math.round(aleatorio(0.8, 1.3) * 100) / 100,
    comportamento: comportamento || sortear(LISTA_NATURAIS),
  };
}

function herdarHabilidades(pai1, pai2) {
  const velocidade = (pai1.velocidadeMod + pai2.velocidadeMod) / 2 + aleatorio(-0.1, 0.1);
  return {
    velocidadeMod: Math.round(limitar(velocidade, VELOCIDADE_MIN, VELOCIDADE_MAX) * 100) / 100,
    comportamento: herdarComportamento(pai1.comportamento, pai2.comportamento),
  };
}

// ============================================================
// bau_dados.py — só a economia básica da Membrana ⬡
// ============================================================
const MEMBRANA_INICIAL = 50;
const CUSTO_ORGANISMO = 1;
const GANHO_FUSAO = 3;
const GANHO_ESPECIE_NOVA = 20;
const GANHO_CLIQUE_SEM_SALDO = 1;
const LIMITE_POPULACAO = 300;
const ORGANISMOS_DA_CONTA_NOVA = 6;

// ============================================================
// placa.py — tamanhos do mapa e da simulação
// ============================================================
const LARGURA_MUNDO = 940 * 3;
const ALTURA_MUNDO = 540 * 2;
const TAMANHO_CELULA_GRADE = 100;
const DISTANCIA_MINIMA_ARRASTO = 4;
const MARGEM = 20;
const VELOCIDADE_CAMERA = 18;
const DISTANCIA_PERSEGUICAO = 250;
const RECARGA_CONTAGIO = 50;
const ESPACO_GRADE_FUNDO = 200;
const VELOCIDADES = [1, 2, 4];
const DURACAO_DO_QUADRO = 40;        // ms: o after(40) do tkinter
const DURACAO_SELO_NOVO = 10000;     // ms que o ❓ de espécie nova fica visível

const LARGURA_MINIMAPA = 180;
const ALTURA_MINIMAPA = Math.round(LARGURA_MINIMAPA * ALTURA_MUNDO / LARGURA_MUNDO);
const TECLAS_SETAS = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };

const ESTILO_SELOS = { "?": ["#f2c94c", "#1a1a1a"], "!": ["#e04848", "#ffffff"] };

const COR = {
  fundo: "#0a2646", painel: "#0f2e4f", grade: "#123a63", borda: "#2a9acc",
  texto: "#d8f1fb", textoSuave: "#8fc3dd", aviso: "#f2c94c",
};

// ============================================================
// camera.py
// ============================================================
const ZOOM_MINIMO = 1.0, ZOOM_MAXIMO = 3.0, PASSO_ZOOM = 0.25;

class Camera {
  constructor(larguraTela, alturaTela) {
    this.larguraTela = larguraTela;
    this.alturaTela = alturaTela;
    this.zoom = 1.0;
    this.x = 0;
    this.y = 0;
  }
  paraTela(x, y) { return [(x - this.x) * this.zoom, (y - this.y) * this.zoom]; }
  paraMundo(xTela, yTela) { return [this.x + xTela / this.zoom, this.y + yTela / this.zoom]; }
  larguraVisivel() { return this.larguraTela / this.zoom; }
  alturaVisivel() { return this.alturaTela / this.zoom; }
  limitar() {
    this.x = Math.max(0, Math.min(LARGURA_MUNDO - this.larguraVisivel(), this.x));
    this.y = Math.max(0, Math.min(ALTURA_MUNDO - this.alturaVisivel(), this.y));
  }
  mover(dxTela, dyTela) {
    this.x += dxTela / this.zoom;
    this.y += dyTela / this.zoom;
    this.limitar();
  }
  centralizarEm(x, y) {
    this.x = x - this.larguraVisivel() / 2;
    this.y = y - this.alturaVisivel() / 2;
    this.limitar();
  }
  aplicarZoom(novoZoom, xTela, yTela) {
    novoZoom = limitar(novoZoom, ZOOM_MINIMO, ZOOM_MAXIMO);
    const [mundoX, mundoY] = this.paraMundo(xTela, yTela);
    this.zoom = novoZoom;
    this.x = mundoX - xTela / this.zoom;
    this.y = mundoY - yTela / this.zoom;
    this.limitar();
  }
}

// ============================================================
// recursos.py — imagens (com a sobra transparente recortada) e sons.py
// ============================================================
const imagensDosEstagios = {};   // estágio -> canvas com o desenho já recortado
let imagemFundo = null;

function carregarImagem(caminho) {
  return new Promise(resolve => {
    const imagem = new Image();
    imagem.onload = () => resolve(imagem);
    imagem.onerror = () => resolve(null);   // sem o PNG, o organismo vira um círculo (igual ao Python)
    imagem.src = caminho;
  });
}

function recortarTransparencia(imagem) {
  // Igual ao _recortar_transparencia: pixels com alfa até 40 não contam como desenho
  const largura = imagem.naturalWidth, altura = imagem.naturalHeight;
  const tela = document.createElement("canvas");
  tela.width = largura;
  tela.height = altura;
  const ctx = tela.getContext("2d");
  ctx.drawImage(imagem, 0, 0);
  let pixels;
  try {
    pixels = ctx.getImageData(0, 0, largura, altura).data;
  } catch (erro) {
    return tela;   // aberto direto do disco (file://) alguns navegadores bloqueiam a leitura: usa sem recortar
  }
  let x0 = largura, y0 = altura, x1 = -1, y1 = -1;
  for (let y = 0; y < altura; y++) {
    for (let x = 0; x < largura; x++) {
      if (pixels[(y * largura + x) * 4 + 3] > 40) {
        if (x < x0) x0 = x;
        if (x > x1) x1 = x;
        if (y < y0) y0 = y;
        if (y > y1) y1 = y;
      }
    }
  }
  if (x1 < 0) return tela;
  const recorte = document.createElement("canvas");
  recorte.width = x1 - x0 + 1;
  recorte.height = y1 - y0 + 1;
  recorte.getContext("2d").drawImage(tela, x0, y0, recorte.width, recorte.height, 0, 0, recorte.width, recorte.height);
  return recorte;
}

async function carregarRecursos() {
  const pedidos = ESTAGIOS.map(async ([_nome, arquivo], indice) => {
    const numero = String(arquivo).padStart(2, "0");
    const imagem = await carregarImagem(`assets/organismos/estagio_${numero}.png`);
    if (imagem) imagensDosEstagios[indice + 1] = recortarTransparencia(imagem);
  });
  pedidos.push(carregarImagem("assets/fundos/simulacao.png").then(imagem => { imagemFundo = imagem; }));
  await Promise.all(pedidos);
}

const SOM_MERGE = "merge", SOM_CLIQUE = "clique", SOM_CORRUPCAO = "corrupcao",
      SOM_CONQUISTA = "conquista", SOM_TROFEU = "trofeu";
const INTERVALO_MINIMO_SOM = 120;   // ms: no 4× acontecem muitas fusões; assim os sons não viram uma "metralhadora"
const sons = {};
const ultimaVezDoSom = {};
let somAtivado = true;

function tocar(nome) {
  if (!somAtivado) return;
  const agora = performance.now();
  if (agora - (ultimaVezDoSom[nome] || -Infinity) < INTERVALO_MINIMO_SOM) return;
  ultimaVezDoSom[nome] = agora;
  if (!sons[nome]) sons[nome] = new Audio(`assets/sons/${nome}.wav`);
  const som = sons[nome].cloneNode();
  som.volume = 0.8;
  som.play().catch(() => {});   // o navegador só deixa tocar depois do primeiro clique do jogador
}

// ============================================================
// organismo.py
// ============================================================
let proximoId = 1;

class Organismo {
  constructor({ id, estagio, x, y, velocidadeMod, comportamento }) {
    this.id = id || proximoId++;
    this.estagio = estagio;
    this.x = x;
    this.y = y;
    this.velocidadeMod = velocidadeMod;
    this.comportamento = comportamento;
    this.recargaContagio = 0;
    this.novoAte = 0;
    this.angulo = aleatorio(0, 2 * Math.PI);
    this.descanso = 0;
    this.passosZigue = 0;
  }

  raio() { return tamanhoDoEstagio(this.estagio) * modificadores(this.comportamento).tamanhoMult; }
  velocidadeEfetiva() { return modificadores(this.comportamento).velocidadeMult * this.velocidadeMod; }
  sofreuInterferencia() { return !modificadores(this.comportamento).natural; }
  marcarComoEspecieNova() { this.novoAte = performance.now() + DURACAO_SELO_NOVO; }

  selo() {
    if (this.novoAte > performance.now()) return "?";
    if (this.sofreuInterferencia()) return "!";
    return null;
  }

  mover(alvo) {
    const movimento = modificadores(this.comportamento).movimento;
    if (movimento === "suave") {
      if (this.descanso > 0) { this.descanso -= 1; return; }
      if (Math.random() < 0.004) this.descanso = inteiroAleatorio(25, 60);
      this.angulo += aleatorio(-0.15, 0.15);
    } else if (movimento === "reto") {
      this.angulo += aleatorio(-0.05, 0.05);
    } else if (movimento === "persegue" && alvo) {
      const anguloAlvo = Math.atan2(alvo.y - this.y, alvo.x - this.x);
      const diferenca = ((anguloAlvo - this.angulo + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
      this.angulo += diferenca * 0.15 + aleatorio(-0.1, 0.1);
    } else if (movimento === "zigue") {
      this.passosZigue += 1;
      if (this.passosZigue >= 10) {
        this.passosZigue = 0;
        this.angulo += sortear([-1.1, 1.1]);
      }
    } else {
      this.angulo += aleatorio(-0.3, 0.3);
    }

    const velocidade = this.velocidadeEfetiva();
    this.x += Math.cos(this.angulo) * velocidade;
    this.y += Math.sin(this.angulo) * velocidade;
    const raio = this.raio();
    if (this.x < MARGEM + raio || this.x > LARGURA_MUNDO - MARGEM - raio) this.angulo = Math.PI - this.angulo;
    if (this.y < MARGEM + raio || this.y > ALTURA_MUNDO - MARGEM - raio) this.angulo = -this.angulo;
    this.x = limitar(this.x, MARGEM + raio, LARGURA_MUNDO - MARGEM - raio);
    this.y = limitar(this.y, MARGEM + raio, ALTURA_MUNDO - MARGEM - raio);
  }

  distanciaPara(outro) { return Math.hypot(this.x - outro.x, this.y - outro.y); }
  estaEncostando(outro) { return this.distanciaPara(outro) <= this.raio() + outro.raio(); }
  contemPonto(x, y) { return Math.hypot(this.x - x, this.y - y) <= Math.max(this.raio(), 6); }

  desenhar(ctx, camera) {
    const [x, y] = camera.paraTela(this.x, this.y);
    const raio = this.raio() * camera.zoom;
    const folga = raio + 40;
    if (x < -folga || y < -folga || x > camera.larguraTela + folga || y > camera.alturaTela + folga) return;

    const imagem = imagensDosEstagios[this.estagio];
    if (imagem) {
      // _encaixar_no_quadrado: o lado maior vira o diâmetro, sem achatar
      const escala = (raio * 2) / Math.max(imagem.width, imagem.height);
      const largura = imagem.width * escala, altura = imagem.height * escala;
      ctx.drawImage(imagem, x - largura / 2, y - altura / 2, largura, altura);
    } else {
      ctx.fillStyle = corDoEstagio(this.estagio);
      ctx.beginPath();
      ctx.arc(x, y, raio, 0, 2 * Math.PI);
      ctx.fill();
    }

    const selo = this.selo();
    if (selo) {
      const raioSelo = 6 + 2 * camera.zoom;
      const sx = x + raio * 0.75, sy = y - raio * 0.75;
      const [corFundo, corTexto] = ESTILO_SELOS[selo];
      ctx.beginPath();
      ctx.arc(sx, sy, raioSelo, 0, 2 * Math.PI);
      ctx.fillStyle = corFundo;
      ctx.fill();
      ctx.strokeStyle = "#1a1a1a";
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = corTexto;
      ctx.font = `bold ${Math.round(raioSelo * 1.5)}px Segoe UI, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(selo, sx, sy + 1);
    }
  }

  paraSalvar() {
    return { id: this.id, estagio: this.estagio, x: Math.round(this.x), y: Math.round(this.y),
             velocidadeMod: this.velocidadeMod, comportamento: this.comportamento };
  }
}

// ============================================================
// persistencia.py — no navegador o save fica no localStorage (sem login, sem SQLite)
// ============================================================
const CHAVE_DO_SAVE = "colonia_web_demo_v1";

function saveVazio() {
  return { membrana: 0, organismos: [], descobertos: [], mergeTotal: 0, demoConcluida: false, somAtivado: true };
}

function carregarSave() {
  try {
    const texto = localStorage.getItem(CHAVE_DO_SAVE);
    if (texto) return Object.assign(saveVazio(), JSON.parse(texto));
  } catch (erro) { /* aba anônima ou dados bloqueados: o jogo funciona, só não guarda */ }
  return saveVazio();
}

function gravarSave() {
  try {
    estado.organismos = jogo.organismos.map(o => o.paraSalvar());
    localStorage.setItem(CHAVE_DO_SAVE, JSON.stringify(estado));
  } catch (erro) { /* idem */ }
}

function apagarSave() {
  try { localStorage.removeItem(CHAVE_DO_SAVE); } catch (erro) { /* idem */ }
}

// ============================================================
// placa.py + simulacao.py — a tela do jogo
// ============================================================
const $ = id => document.getElementById(id);
const canvas = $("placa");
const ctx = canvas.getContext("2d");

let estado = carregarSave();
somAtivado = estado.somAtivado !== false;

const jogo = {
  organismos: [],
  camera: new Camera(940, 540),
  pausado: false,
  velocidade: 1,
  contadorCiclos: 0,
  contadorQuadros: 0,
  arrastando: null,
  inicioClique: null,
  moveuMouse: false,
  arrastoCamera: null,
  arrastandoMinimapa: false,
  teclasApertadas: new Set(),
  ganhos: [],                  // os "+3 ⬡" que sobem e somem
  trofeuAgendado: false,
  janelaAberta: false,
};

// ---------- organismos ----------

function posicaoAleatoria() {
  const margem = 40, camera = jogo.camera;
  return [aleatorio(camera.x + margem, camera.x + camera.larguraVisivel() - margem),
          aleatorio(camera.y + margem, camera.y + camera.alturaVisivel() - margem)];
}

function criarEMostrar(estagio, x, y, habilidades) {
  if (x === undefined) [x, y] = posicaoAleatoria();
  habilidades = habilidades || gerarHabilidadesIniciais();
  const novo = new Organismo({ estagio, x, y, velocidadeMod: habilidades.velocidadeMod,
                               comportamento: habilidades.comportamento });
  jogo.organismos.push(novo);
  novo.ganhoDescoberta = registrarDescoberta(novo);
  if (novo.ganhoDescoberta) {
    mostrarEvento(`❓ Nova espécie: ${nomeDoEstagio(estagio)}! (+${novo.ganhoDescoberta} ⬡)`);
    mostrarGanho(novo.x, novo.y - novo.raio(), novo.ganhoDescoberta);
  }
  atualizarRotulos();
  return novo;
}

function removerOrganismo(organismo) {
  const indice = jogo.organismos.indexOf(organismo);
  if (indice >= 0) jogo.organismos.splice(indice, 1);
  if (jogo.arrastando === organismo) jogo.arrastando = null;
  atualizarRotulos();
}

function registrarDescoberta(organismo) {
  // Primeira vez que este estágio aparece? Dá Membrana e, no estágio 10, agenda o fim da demo
  if (estado.descobertos.includes(organismo.estagio)) return 0;
  estado.descobertos.push(organismo.estagio);
  organismo.marcarComoEspecieNova();
  ganhar(GANHO_ESPECIE_NOVA);
  tocar(SOM_CONQUISTA);
  atualizarRecorde();
  if (organismo.estagio >= ESTAGIO_FINAL_DA_DEMO && !estado.demoConcluida && !jogo.trofeuAgendado) {
    jogo.trofeuAgendado = true;
    mostrarEvento("🏆 BACTÉRIA ÁPICE ALCANÇADA! Preparando o troféu…");
    setTimeout(concluirDemo, 2500);
  }
  return GANHO_ESPECIE_NOVA;
}

function semearOrganismosIniciais() {
  // começo de conta: alguns organismos calmos do estágio 1, no meio do mapa
  for (let i = 0; i < ORGANISMOS_DA_CONTA_NOVA; i++) criarEMostrar(1, undefined, undefined, gerarHabilidadesIniciais("Calmo"));
}

function carregarInicial() {
  if (estado.organismos.length === 0 && estado.mergeTotal === 0 && estado.descobertos.length === 0) {
    estado.membrana = MEMBRANA_INICIAL;
    semearOrganismosIniciais();
    mostrarEvento("Organismos iguais que se encostam se fundem e evoluem. Chegue à Bactéria Ápice!");
  } else {
    jogo.organismos = estado.organismos.slice(0, LIMITE_POPULACAO).map(linha => new Organismo(linha));
    proximoId = jogo.organismos.reduce((maior, o) => Math.max(maior, o.id), 0) + 1;
  }
}

// ---------- Membrana ----------

function ganhar(quantidade) {
  estado.membrana += quantidade;
  atualizarRotulos();
  return quantidade;
}

function gastarMembrana(quantidade) {
  if (estado.membrana < quantidade) return false;
  estado.membrana -= quantidade;
  atualizarRotulos();
  return true;
}

function mostrarGanho(xMundo, yMundo, quantidade) {
  jogo.ganhos.push({ xMundo, yMundo, texto: `+${quantidade} ⬡`, inicio: performance.now() });
}

// ---------- rótulos e avisos ----------

function atualizarRotulos() {
  $("membrana").textContent = `⬡ ${estado.membrana}`;
  $("populacao").textContent = `População: ${jogo.organismos.length}`;
}

function atualizarRecorde() {
  const maior = Math.max(0, ...estado.descobertos);
  $("recorde").textContent = estado.demoConcluida
    ? "🏆 Demo concluída!"
    : `Recorde: estágio ${maior} de ${ESTAGIO_FINAL_DA_DEMO}`;
}

let idApagarEvento = null;
function mostrarEvento(texto) {
  $("evento").textContent = texto;
  // cancela o "apagar" do aviso anterior, senão ele apagaria este aviso novo antes da hora
  clearTimeout(idApagarEvento);
  idApagarEvento = setTimeout(() => { $("evento").textContent = ""; }, 3000);
}

// ---------- simulação ----------

function construirGradeEspacial() {
  const grade = new Map();
  jogo.organismos.forEach((organismo, indice) => {
    const chave = `${Math.floor(organismo.x / TAMANHO_CELULA_GRADE)},${Math.floor(organismo.y / TAMANHO_CELULA_GRADE)}`;
    if (!grade.has(chave)) grade.set(chave, []);
    grade.get(chave).push(indice);
  });
  return grade;
}

function vizinhosDaCelula(grade, cx, cy, alcance = 1) {
  const indices = [];
  for (let dx = -alcance; dx <= alcance; dx++) {
    for (let dy = -alcance; dy <= alcance; dy++) {
      const celula = grade.get(`${cx + dx},${cy + dy}`);
      if (celula) indices.push(...celula);
    }
  }
  return indices;
}

function celulaDe(organismo) {
  return [Math.floor(organismo.x / TAMANHO_CELULA_GRADE), Math.floor(organismo.y / TAMANHO_CELULA_GRADE)];
}

function vizinhoMaisProximo(organismo, grade) {
  const [cx, cy] = celulaDe(organismo);
  const alcance = Math.ceil(DISTANCIA_PERSEGUICAO / TAMANHO_CELULA_GRADE);
  let maisPerto = null, menorDistancia = DISTANCIA_PERSEGUICAO;
  for (const j of vizinhosDaCelula(grade, cx, cy, alcance)) {
    const outro = jogo.organismos[j];
    if (outro === organismo) continue;
    const distancia = organismo.distanciaPara(outro);
    if (distancia < menorDistancia) { maisPerto = outro; menorDistancia = distancia; }
  }
  return maisPerto;
}

function moverTodos(grade) {
  for (const organismo of jogo.organismos) {
    if (organismo.recargaContagio > 0) organismo.recargaContagio -= 1;
    if (organismo === jogo.arrastando) continue;
    const alvo = modificadores(organismo.comportamento).movimento === "persegue" ? vizinhoMaisProximo(organismo, grade) : null;
    organismo.mover(alvo);
  }
}

function aplicarSeparacao(grade) {
  for (const [chave, indicesDaCelula] of grade) {
    const [cx, cy] = chave.split(",").map(Number);
    const indicesVizinhos = vizinhosDaCelula(grade, cx, cy);
    for (const i of indicesDaCelula) {
      const a = jogo.organismos[i];
      if (a === jogo.arrastando) continue;
      const raioA = a.raio();
      for (const j of indicesVizinhos) {
        if (j === i) continue;
        const b = jogo.organismos[j];
        const diferencaX = a.x - b.x, diferencaY = a.y - b.y;
        const distancia = Math.hypot(diferencaX, diferencaY);
        const minimo = (raioA + b.raio()) * 0.9;
        if (distancia <= 0 || distancia >= minimo) continue;
        // o Irritado empurra mais forte quem está perto dele
        const forca = b.comportamento === "Irritado" ? 0.8 : 0.5;
        const sobreposicao = (minimo - distancia) * forca;
        a.x += (diferencaX / distancia) * sobreposicao;
        a.y += (diferencaY / distancia) * sobreposicao;
        a.x = limitar(a.x, MARGEM + raioA, LARGURA_MUNDO - MARGEM - raioA);
        a.y = limitar(a.y, MARGEM + raioA, ALTURA_MUNDO - MARGEM - raioA);
      }
    }
  }
}

function processarColisoes(grade) {
  const usados = new Set();
  const eventos = [];
  for (const [chave, indicesDaCelula] of grade) {
    const [cx, cy] = chave.split(",").map(Number);
    const indicesVizinhos = vizinhosDaCelula(grade, cx, cy);
    for (const i of indicesDaCelula) {
      const a = jogo.organismos[i];
      if (usados.has(a.id)) continue;
      for (const j of indicesVizinhos) {
        if (j <= i) continue;
        const b = jogo.organismos[j];
        if (usados.has(b.id) || a.estagio !== b.estagio || !a.estaEncostando(b)) continue;
        usados.add(a.id);
        usados.add(b.id);
        eventos.push([a, b]);
        break;
      }
    }
  }
  for (const [a, b] of eventos) resolverInteracao(a, b);
}

function resolverInteracao(a, b) {
  // na placa: fusão espontânea (merge). Dois iguais viram um do estágio seguinte
  if (a.estagio >= TOTAL_ESTAGIOS) return;
  const habilidadesNovas = herdarHabilidades(a, b);
  const novoEstagio = a.estagio + 1;
  const x = (a.x + b.x) / 2 + aleatorio(-10, 10);
  const y = (a.y + b.y) / 2 + aleatorio(-10, 10);
  removerOrganismo(a);
  removerOrganismo(b);
  const novo = criarEMostrar(novoEstagio, x, y, habilidadesNovas);
  estado.mergeTotal += 1;
  const ganho = ganhar(GANHO_FUSAO);
  mostrarGanho(x, y - novo.raio(), ganho);
  if (!novo.ganhoDescoberta) mostrarEvento(`Fusão espontânea: ${nomeDoEstagio(novoEstagio)} (+${ganho} ⬡)`);
  tocar(SOM_MERGE);
}

function espalharInfeccao(grade) {
  const novosInfectados = [];
  for (const [chave, indicesDaCelula] of grade) {
    const [cx, cy] = chave.split(",").map(Number);
    const indicesVizinhos = vizinhosDaCelula(grade, cx, cy);
    for (const i of indicesDaCelula) {
      const doente = jogo.organismos[i];
      if (doente.comportamento !== "Infectado" || doente.recargaContagio > 0) continue;
      for (const j of indicesVizinhos) {
        const outro = jogo.organismos[j];
        if (outro === doente || outro.comportamento === "Infectado") continue;
        if (novosInfectados.includes(outro) || !doente.estaEncostando(outro)) continue;
        doente.recargaContagio = RECARGA_CONTAGIO;
        if (Math.random() < COMPORTAMENTOS["Infectado"].chanceContagio) novosInfectados.push(outro);
        break;
      }
    }
  }
  for (const organismo of novosInfectados) {
    organismo.comportamento = "Infectado";
    mostrarEvento(`☣️ Contágio: um ${nomeDoEstagio(organismo.estagio)} foi infectado`);
  }
  if (novosInfectados.length) tocar(SOM_CORRUPCAO);
}

function passoDaSimulacao() {
  moverTodos(construirGradeEspacial());
  let grade = construirGradeEspacial();
  aplicarSeparacao(grade);
  processarColisoes(grade);
  grade = construirGradeEspacial();
  espalharInfeccao(grade);
  jogo.contadorCiclos += 1;
  if (jogo.contadorCiclos % 50 === 0) gravarSave();   // ~2 segundos no 1×
}

function moverCameraPelasTeclas() {
  let dx = 0, dy = 0;
  for (const tecla of jogo.teclasApertadas) {
    dx += TECLAS_SETAS[tecla][0];
    dy += TECLAS_SETAS[tecla][1];
  }
  if (dx || dy) jogo.camera.mover(dx * VELOCIDADE_CAMERA, dy * VELOCIDADE_CAMERA);
}

// ---------- desenho ----------

function desenharTudo() {
  const camera = jogo.camera;
  const larguraTela = camera.larguraTela, alturaTela = camera.alturaTela;
  ctx.fillStyle = COR.fundo;
  ctx.fillRect(0, 0, larguraTela, alturaTela);
  if (imagemFundo) ctx.drawImage(imagemFundo, 0, 0, larguraTela, alturaTela);

  // linhas do fundo e borda do mapa acompanham a câmera
  const [x0, y0] = camera.paraTela(0, 0);
  const [x1, y1] = camera.paraTela(LARGURA_MUNDO, ALTURA_MUNDO);
  ctx.strokeStyle = COR.grade;
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = ESPACO_GRADE_FUNDO; x < LARGURA_MUNDO; x += ESPACO_GRADE_FUNDO) {
    const [xt] = camera.paraTela(x, 0);
    ctx.moveTo(xt, y0);
    ctx.lineTo(xt, y1);
  }
  for (let y = ESPACO_GRADE_FUNDO; y < ALTURA_MUNDO; y += ESPACO_GRADE_FUNDO) {
    const [, yt] = camera.paraTela(0, y);
    ctx.moveTo(x0, yt);
    ctx.lineTo(x1, yt);
  }
  ctx.stroke();
  ctx.strokeStyle = COR.borda;
  ctx.lineWidth = 3;
  ctx.strokeRect(x0 + 2, y0 + 2, x1 - x0 - 4, y1 - y0 - 4);

  for (const organismo of jogo.organismos) organismo.desenhar(ctx, camera);

  desenharGanhos();

  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  if (!jogo.organismos.length) {
    ctx.fillStyle = COR.textoSuave;
    ctx.font = "italic 16px Segoe UI, sans-serif";
    ctx.fillText("Placa vazia nesta região.", larguraTela / 2, alturaTela / 2 - 11);
    ctx.fillText("Clique em “+ Organismo” ou use o minimapa para procurar.", larguraTela / 2, alturaTela / 2 + 11);
  }
  if (jogo.pausado) {
    ctx.fillStyle = COR.aviso;
    ctx.font = "bold 16px Segoe UI, sans-serif";
    ctx.fillText("⏸  PAUSADO  —  Espaço para continuar", larguraTela / 2, 22);
  }

  desenharMinimapa();
}

function desenharGanhos() {
  // um "+3 ⬡" sobe 33 px e some (no Python: 22 passos de 1,5 px a cada 35 ms)
  const agora = performance.now();
  jogo.ganhos = jogo.ganhos.filter(g => agora - g.inicio < 770);
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.font = "bold 15px Segoe UI, sans-serif";
  ctx.fillStyle = COR.aviso;
  for (const ganho of jogo.ganhos) {
    const [x, y] = jogo.camera.paraTela(ganho.xMundo, ganho.yMundo);
    ctx.fillText(ganho.texto, x, y - ((agora - ganho.inicio) / 770) * 33);
  }
}

function areaMinimapa() {
  const x0 = jogo.camera.larguraTela - LARGURA_MINIMAPA - 10;
  const y0 = jogo.camera.alturaTela - ALTURA_MINIMAPA - 10;
  return [x0, y0, x0 + LARGURA_MINIMAPA, y0 + ALTURA_MINIMAPA];
}

function desenharMinimapa() {
  const camera = jogo.camera;
  const [x0, y0] = areaMinimapa();
  const escala = LARGURA_MINIMAPA / LARGURA_MUNDO;
  ctx.fillStyle = COR.painel;
  ctx.fillRect(x0, y0, LARGURA_MINIMAPA, ALTURA_MINIMAPA);
  ctx.strokeStyle = COR.borda;
  ctx.lineWidth = 2;
  ctx.strokeRect(x0, y0, LARGURA_MINIMAPA, ALTURA_MINIMAPA);
  for (const organismo of jogo.organismos) {
    const r = Math.max(1.5, organismo.raio() * escala * 1.5);
    ctx.fillStyle = organismo.sofreuInterferencia() ? "#e04848" : corDoEstagio(organismo.estagio);
    ctx.beginPath();
    ctx.arc(x0 + organismo.x * escala, y0 + organismo.y * escala, r, 0, 2 * Math.PI);
    ctx.fill();
  }
  ctx.strokeStyle = "#f2f2f2";
  ctx.lineWidth = 1;
  ctx.strokeRect(x0 + camera.x * escala, y0 + camera.y * escala,
                 camera.larguraVisivel() * escala, camera.alturaVisivel() * escala);
}

function ajustarTamanhoDoCanvas() {
  // a área do jogo ocupa o espaço que sobrar; a câmera passa a mostrar um pedaço maior ou menor do mapa
  const caixa = $("area").getBoundingClientRect();
  const largura = Math.max(1, Math.floor(caixa.width - 2)), altura = Math.max(1, Math.floor(caixa.height - 2));
  const densidade = window.devicePixelRatio || 1;
  canvas.width = Math.round(largura * densidade);
  canvas.height = Math.round(altura * densidade);
  ctx.setTransform(densidade, 0, 0, densidade, 0, 0);
  ctx.imageSmoothingQuality = "high";
  jogo.camera.larguraTela = largura;
  jogo.camera.alturaTela = altura;
  jogo.camera.limitar();
}

// ---------- o loop (o after(40) do tkinter vira requestAnimationFrame com passo fixo) ----------

let ultimoInstante = null, acumulado = 0;

function ciclo(instante) {
  if (ultimoInstante === null) ultimoInstante = instante;
  // se a aba ficou escondida, não tenta "recuperar" o tempo perdido de uma vez só
  acumulado = Math.min(acumulado + (instante - ultimoInstante), DURACAO_DO_QUADRO * 5);
  ultimoInstante = instante;
  while (acumulado >= DURACAO_DO_QUADRO) {
    acumulado -= DURACAO_DO_QUADRO;
    moverCameraPelasTeclas();
    if (!jogo.pausado && !jogo.janelaAberta) {
      for (let passo = 0; passo < jogo.velocidade; passo++) passoDaSimulacao();
    }
  }
  desenharTudo();
  requestAnimationFrame(ciclo);
}

// ============================================================
// janelas.py — avisos e perguntas, no estilo da janela dos troféus
// ============================================================
function abrirJanela({ emoji = "", titulo = "", subtitulo = "", linhas = "", frase = "", cor = COR.borda, botoes }) {
  return new Promise(resolve => {
    jogo.janelaAberta = true;
    fecharMenu();
    const janela = $("janela");
    janela.style.setProperty("--cor-janela", cor);
    janela.innerHTML = "";
    const adicionar = (tag, classe, texto) => {
      if (!texto) return;
      const elemento = document.createElement(tag);
      if (classe) elemento.className = classe;
      elemento.textContent = texto;
      janela.appendChild(elemento);
    };
    adicionar("div", "emoji", emoji);
    adicionar("h3", "", titulo);
    adicionar("p", "subtitulo", subtitulo);
    adicionar("div", "caixa", linhas);
    adicionar("div", "frase", frase);
    const areaBotoes = document.createElement("div");
    areaBotoes.className = "botoes";
    (botoes || [{ texto: "OK", valor: true }]).forEach((dados, indice) => {
      const botao = document.createElement("button");
      botao.textContent = dados.texto;
      if (indice > 0) botao.className = "secundario";
      botao.onclick = () => fechar(dados.valor);
      areaBotoes.appendChild(botao);
    });
    janela.appendChild(areaBotoes);
    $("cobertura").hidden = false;
    areaBotoes.firstChild.focus();

    function fechar(valor) {
      $("cobertura").hidden = true;
      jogo.janelaAberta = false;
      document.removeEventListener("keydown", aoTeclar, true);
      resolve(valor);
    }
    function aoTeclar(evento) {
      if (evento.key === "Escape") { evento.preventDefault(); fechar(false); }
    }
    document.addEventListener("keydown", aoTeclar, true);
  });
}

function perguntar(titulo, texto) {
  return abrirJanela({ emoji: "❔", titulo, linhas: texto,
                       botoes: [{ texto: "Sim", valor: true }, { texto: "Não", valor: false }] });
}

// ============================================================
// ações do jogador (simulacao.py)
// ============================================================
function adicionarOrganismoAleatorio() {
  if (jogo.organismos.length >= LIMITE_POPULACAO) {
    mostrarEvento("Colônia no limite — não cabe mais ninguém");
    return;
  }
  const semSaida = estado.membrana < CUSTO_ORGANISMO && !jogo.organismos.length;
  if (!semSaida && !gastarMembrana(CUSTO_ORGANISMO)) {
    mostrarEvento("Sem Membrana! Clique num organismo da placa para ganhar +1 ⬡");
    return;
  }
  criarEMostrar(1);
  tocar(SOM_CLIQUE);
  if (semSaida) mostrarEvento("Este saiu de graça: sem Membrana e com a placa vazia 🤝");
}

function aoClicarOrganismo(organismo) {
  // sem Membrana nenhuma, clicar num organismo "brota" +1 ⬡ (assim o jogador nunca fica preso)
  if (estado.membrana < CUSTO_ORGANISMO) {
    mostrarGanho(organismo.x, organismo.y - organismo.raio(), ganhar(GANHO_CLIQUE_SEM_SALDO));
    tocar(SOM_CLIQUE);
    return;
  }
  inspecionar(organismo);
}

function inspecionar(organismo) {
  const bloco = blocoDoEstagio(organismo.estagio);
  const comportamento = modificadores(organismo.comportamento);
  abrirJanela({
    emoji: bloco.emoji,
    titulo: "Inspeção de Organismo",
    subtitulo: `Estágio ${organismo.estagio}: ${nomeDoEstagio(organismo.estagio)} (${bloco.nome})`,
    linhas: [
      `Comportamento: ${comportamento.emoji} ${organismo.comportamento}`,
      `   ${comportamento.descricao}`,
      `Velocidade: ${Math.round(organismo.velocidadeEfetiva() * 100) / 100}`,
      `Tamanho: ${Math.round(organismo.raio() * 2)} px`,
    ].join("\n"),
  });
}

function infectar(organismo) {
  if (organismo.comportamento === "Infectado") {
    mostrarEvento("Esse organismo já está infectado.");
    return;
  }
  organismo.comportamento = "Infectado";
  mostrarEvento("Organismo infectado ☣️");
  tocar(SOM_CORRUPCAO);
}

function destruir(organismo) {
  removerOrganismo(organismo);
  mostrarEvento("Organismo destruído");
}

async function confirmarLimpar() {
  if (await perguntar("Limpar Placa", "Remover todos os organismos da placa?")) {
    jogo.organismos = [];
    atualizarRotulos();
    gravarSave();
  }
}

async function confirmarRecomecar() {
  const sim = await perguntar("Recomeçar demo",
    "Apagar a colônia, a Membrana e as espécies descobertas e começar do zero?");
  if (!sim) return;
  apagarSave();
  estado = saveVazio();
  estado.somAtivado = somAtivado;
  jogo.organismos = [];
  jogo.trofeuAgendado = false;
  jogo.camera.zoom = 1;
  $("zoom-rotulo").textContent = "100%";
  jogo.camera.centralizarEm(LARGURA_MUNDO / 2, ALTURA_MUNDO / 2);
  carregarInicial();
  atualizarRecorde();
  gravarSave();
}

async function concluirDemo() {
  // a janela de festa do troféu (main.py, _mostrar_comemoracao), adaptada para a demo
  estado.demoConcluida = true;
  gravarSave();
  atualizarRecorde();
  tocar(SOM_TROFEU);
  await abrirJanela({
    emoji: "🦠",
    cor: "#7fe7ff",
    titulo: "🎉 VOCÊ COMPLETOU A DEMO! 🎉",
    subtitulo: "Você chegou à Bactéria Ápice (estágio 10)",
    linhas: [
      "Isso é só o primeiro bloco da evolução.",
      "",
      "Na versão completa (Windows), você ainda tem:",
      "   ✴️ os Vírus e 🧫 as Células Complexas, até a Forma de Vida Suprema",
      "   ⚗️ Área de Fusão e 🧬 Área de Mutação",
      "   📦 o Baú, com upgrades e frascos de herói e de vilão",
      "   🤖 IAs: Guardião, Predador e Simbionte",
      "   🏆 5 troféus, até o 💎 Diamante e o título de Mestre da Colônia",
      "",
      "Baixe o jogo nesta mesma página do itch.io. 😉",
      "Aqui, a sua colônia continua do jeito que está: jogue livremente.",
    ].join("\n"),
    frase: "🍀 Obrigado por jogar, cientista!",
    botoes: [{ texto: "Continuar ▶", valor: true }],
  });
}

// ---------- barra lateral: as outras telas ficam na versão completa ----------

const TELAS = [
  ["Simulação", "🔬", null],
  ["Área de Fusão", "⚗️", "Iguais que se encostam aqui se reproduzem. Leve os filhotes de volta à placa para fundir."],
  ["Área de Mutação", "🧬", "Crie Mutações que pulam +2 estágios. Abre com o troféu de 🌲 Madeira."],
  ["Baú", "📦", "Gaste a Membrana ⬡ em upgrades permanentes e em frascos de herói ou de vilão."],
  ["Geladeira", "🧊", "Guarde até 6 cenários da sua colônia para carregar depois."],
  ["Manual", "📖", "Todas as espécies, receitas e comportamentos que você já descobriu."],
  ["Diário", "📔", "O registro de tudo o que aconteceu nos seus experimentos."],
  ["Conquistas", "🏅", "Dezenas de conquistas, algumas dão upgrades de presente."],
  ["Troféus", "🏆", "5 troféus, da 🌲 Madeira ao 💎 Diamante. Cada um libera algo novo."],
];

function montarBarraLateral() {
  const navegacao = $("navegacao");
  for (const [nome, icone, descricao] of TELAS) {
    const botao = document.createElement("button");
    botao.className = "nav" + (descricao ? " trancado" : " ativo");
    botao.textContent = `${icone}  ${nome}${descricao ? "  🔒" : ""}`;
    if (descricao) {
      botao.onclick = () => abrirJanela({
        emoji: icone, titulo: `${nome} 🔒`, subtitulo: "Disponível na versão completa (Windows)",
        linhas: `${descricao}\n\nBaixe o jogo completo nesta mesma página do itch.io.`,
      });
    }
    navegacao.appendChild(botao);
  }
}

function atualizarBotaoSom() {
  $("som").textContent = somAtivado ? "🔊  Som: ligado" : "🔇  Som: desligado";
}

// ---------- pausa, velocidade e zoom ----------

function alternarPausa() {
  jogo.pausado = !jogo.pausado;
  $("pausa").textContent = jogo.pausado ? "▶ Continuar" : "⏸ Pausar";
  $("pausa").classList.toggle("ligado", jogo.pausado);
  if (jogo.pausado) gravarSave();
}

function alternarVelocidade() {
  // 1× → 2× → 4× → 1×. No 4×, cada quadro faz 4 passos da simulação
  jogo.velocidade = VELOCIDADES[(VELOCIDADES.indexOf(jogo.velocidade) + 1) % VELOCIDADES.length];
  $("velocidade").textContent = `⏩ ${jogo.velocidade}×`;
  $("velocidade").classList.toggle("ligado", jogo.velocidade > 1);
}

function mudarZoom(novoZoom, xTela, yTela) {
  if (xTela === undefined) { xTela = jogo.camera.larguraTela / 2; yTela = jogo.camera.alturaTela / 2; }
  jogo.camera.aplicarZoom(novoZoom, xTela, yTela);
  $("zoom-rotulo").textContent = `${Math.round(jogo.camera.zoom * 100)}%`;
}

// ---------- menu do botão direito ----------

function abrirMenu(organismo, xPagina, yPagina) {
  const menu = $("menu");
  const dados = modificadores(organismo.comportamento);
  menu.innerHTML = "";
  const titulo = document.createElement("div");
  titulo.className = "titulo-menu";
  titulo.textContent = `${nomeDoEstagio(organismo.estagio)}  •  ${dados.emoji} ${organismo.comportamento}`;
  menu.appendChild(titulo);
  const opcoes = [["🔍  Inspecionar", inspecionar], ["☣️  Infectar", infectar], ["💥  Destruir", destruir]];
  for (const [texto, acao] of opcoes) {
    const botao = document.createElement("button");
    botao.textContent = texto;
    botao.onclick = () => {
      fecharMenu();
      if (!jogo.organismos.includes(organismo)) { mostrarEvento("Esse organismo não está mais aqui."); return; }
      acao(organismo);
    };
    menu.appendChild(botao);
  }
  menu.hidden = false;
  // não deixa o menu sair da janela
  const largura = menu.offsetWidth, altura = menu.offsetHeight;
  menu.style.left = `${Math.min(xPagina, window.innerWidth - largura - 4)}px`;
  menu.style.top = `${Math.min(yPagina, window.innerHeight - altura - 4)}px`;
}

function fecharMenu() { $("menu").hidden = true; }

// ---------- mouse: arrastar, clicar e mover a câmera ----------

function posicaoNoCanvas(evento) {
  const caixa = canvas.getBoundingClientRect();
  return [evento.clientX - caixa.left, evento.clientY - caixa.top];
}

function estaNoMinimapa(x, y) {
  const [x0, y0, x1, y1] = areaMinimapa();
  return x0 <= x && x <= x1 && y0 <= y && y <= y1;
}

function irPeloMinimapa(x, y) {
  const [x0, y0] = areaMinimapa();
  const escala = LARGURA_MINIMAPA / LARGURA_MUNDO;
  jogo.camera.centralizarEm((x - x0) / escala, (y - y0) / escala);
}

function organismoEm(xTela, yTela) {
  const [x, y] = jogo.camera.paraMundo(xTela, yTela);
  for (let i = jogo.organismos.length - 1; i >= 0; i--) {
    if (jogo.organismos[i].contemPonto(x, y)) return jogo.organismos[i];
  }
  return null;
}

canvas.addEventListener("pointerdown", evento => {
  if (evento.button !== 0) return;
  fecharMenu();
  canvas.setPointerCapture(evento.pointerId);
  const [x, y] = posicaoNoCanvas(evento);
  jogo.inicioClique = [x, y];
  jogo.moveuMouse = false;
  if (estaNoMinimapa(x, y)) {
    jogo.arrastandoMinimapa = true;
    irPeloMinimapa(x, y);
    return;
  }
  jogo.arrastando = organismoEm(x, y);
  if (!jogo.arrastando) jogo.arrastoCamera = [x, y, jogo.camera.x, jogo.camera.y];
});

canvas.addEventListener("pointermove", evento => {
  if (!jogo.inicioClique) return;
  const [x, y] = posicaoNoCanvas(evento);
  if (jogo.arrastandoMinimapa) { irPeloMinimapa(x, y); return; }
  if (!jogo.moveuMouse) {
    if (Math.hypot(x - jogo.inicioClique[0], y - jogo.inicioClique[1]) < DISTANCIA_MINIMA_ARRASTO) return;
    jogo.moveuMouse = true;
  }
  if (jogo.arrastando) {
    const organismo = jogo.arrastando;
    const [xMundo, yMundo] = jogo.camera.paraMundo(x, y);
    const raio = organismo.raio();
    organismo.x = limitar(xMundo, MARGEM + raio, LARGURA_MUNDO - MARGEM - raio);
    organismo.y = limitar(yMundo, MARGEM + raio, ALTURA_MUNDO - MARGEM - raio);
  } else if (jogo.arrastoCamera) {
    const [x0, y0, cameraX, cameraY] = jogo.arrastoCamera;
    jogo.camera.x = cameraX - (x - x0) / jogo.camera.zoom;
    jogo.camera.y = cameraY - (y - y0) / jogo.camera.zoom;
    jogo.camera.limitar();
  }
});

canvas.addEventListener("pointerup", () => {
  if (!jogo.inicioClique) return;
  if (jogo.arrastando && !jogo.moveuMouse) aoClicarOrganismo(jogo.arrastando);
  jogo.arrastando = null;
  jogo.arrastoCamera = null;
  jogo.arrastandoMinimapa = false;
  jogo.inicioClique = null;
});

canvas.addEventListener("contextmenu", evento => {
  evento.preventDefault();
  const [x, y] = posicaoNoCanvas(evento);
  const organismo = organismoEm(x, y);
  if (organismo) abrirMenu(organismo, evento.clientX, evento.clientY);
  else fecharMenu();
});

canvas.addEventListener("wheel", evento => {
  evento.preventDefault();   // senão a página do itch.io rola junto
  const [x, y] = posicaoNoCanvas(evento);
  mudarZoom(jogo.camera.zoom + (evento.deltaY < 0 ? PASSO_ZOOM : -PASSO_ZOOM), x, y);
}, { passive: false });

document.addEventListener("pointerdown", evento => {
  if (!$("menu").contains(evento.target)) fecharMenu();
});

// ---------- teclado: setas e pausa ----------

document.addEventListener("keydown", evento => {
  if (jogo.janelaAberta) return;
  if (evento.key in TECLAS_SETAS) {
    evento.preventDefault();   // as setas e o espaço também rolariam a página do itch.io
    jogo.teclasApertadas.add(evento.key);
  } else if (evento.key === " ") {
    evento.preventDefault();
    if (!evento.repeat) alternarPausa();
  } else if (evento.key === "Escape") {
    fecharMenu();
  }
});
document.addEventListener("keyup", evento => jogo.teclasApertadas.delete(evento.key));
window.addEventListener("blur", () => jogo.teclasApertadas.clear());

// ---------- botões ----------

$("adicionar").onclick = adicionarOrganismoAleatorio;
$("limpar").onclick = confirmarLimpar;
$("pausa").onclick = alternarPausa;
$("velocidade").onclick = alternarVelocidade;
$("zoom-mais").onclick = () => mudarZoom(jogo.camera.zoom + PASSO_ZOOM);
$("zoom-menos").onclick = () => mudarZoom(jogo.camera.zoom - PASSO_ZOOM);
$("recomecar").onclick = confirmarRecomecar;
$("som").onclick = () => {
  somAtivado = !somAtivado;
  estado.somAtivado = somAtivado;
  atualizarBotaoSom();
  gravarSave();
};
// os botões não ficam com o foco: assim o Espaço pausa o jogo em vez de "apertar" o último botão clicado
document.querySelectorAll("button").forEach(botao => botao.addEventListener("mouseup", () => botao.blur()));

// salva ao sair da página ou trocar de aba
window.addEventListener("pagehide", gravarSave);
document.addEventListener("visibilitychange", () => { if (document.hidden) gravarSave(); });
new ResizeObserver(ajustarTamanhoDoCanvas).observe($("area"));

// ============================================================
// main.py — começa o jogo
// ============================================================
async function iniciar() {
  montarBarraLateral();
  atualizarBotaoSom();
  ajustarTamanhoDoCanvas();
  jogo.camera.centralizarEm(LARGURA_MUNDO / 2, ALTURA_MUNDO / 2);
  await carregarRecursos();
  carregarInicial();
  atualizarRotulos();
  atualizarRecorde();
  requestAnimationFrame(ciclo);
}

iniciar();
