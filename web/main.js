import * as THREE from "three";

/* ---------- luật chơi (khớp với gui/basic_rules.py) ---------- */
const LIST = ["UP", "RIGHT", "DOWN", "LEFT"];
const cellsOf = ([r, c, o]) => (o === "S" ? [[r, c]] : o === "H" ? [[r, c], [r, c + 1]] : [[r, c], [r + 1, c]]);
function roll([r, c, o], d) {
  const T = {
    S: { UP: [r - 2, c, "V"], DOWN: [r + 1, c, "V"], LEFT: [r, c - 2, "H"], RIGHT: [r, c + 1, "H"] },
    H: { UP: [r - 1, c, "H"], DOWN: [r + 1, c, "H"], LEFT: [r, c - 1, "S"], RIGHT: [r, c + 2, "S"] },
    V: { UP: [r - 1, c, "S"], DOWN: [r + 2, c, "S"], LEFT: [r, c - 1, "V"], RIGHT: [r, c + 1, "V"] },
  };
  return T[o][d];
}
function makeLevel(d) {
  const g = d.grid;
  let start, goal;
  g.forEach((row, r) => [...row].forEach((ch, c) => {
    if (ch === "S") start = [r, c, "S"];
    if (ch === "G") goal = [r, c];
  }));
  const tile = (r, c) => (g[r] && g[r][c]) || ".";
  return {
    ...d, rows: g.length, cols: Math.max(...g.map((x) => x.length)), start, goal, tile,
    walk: (r, c) => "OSG".includes(tile(r, c)) || (bridgeAt.has(r + "," + c) && bridgeOpen.has(bridgeAt.get(r + "," + c)))
  };
}

/* ---------- scene ---------- */
const CREAM = 0xfff9c4;
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setClearColor(0x000000, 0);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene();

function gradTex(top, bottom) {
  const c = document.createElement("canvas"); c.width = 4; c.height = 256;
  const g = c.getContext("2d"), gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, top); gr.addColorStop(1, bottom); g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

/* nền do CSS đảm nhiệm: mây, hoa, bụi lấp lánh nằm sau canvas */

const cam = new THREE.PerspectiveCamera(40, 1, 0.1, 200);


/* three.js r155+ không còn nhân π cho đèn: cường độ 1 chỉ sáng ~32% màu thật. Nên phải đặt cường độ ~π lần */
scene.add(new THREE.HemisphereLight(0xffffff, 0xfff8e7, 1.9));
const sun = new THREE.DirectionalLight(0xffffff, 1.4);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.bias = -0.0006;
scene.add(sun, sun.target);

/* ---------- hình khối ---------- */
function slab(w, d, h, r, bev) {          // tấm bo góc, trục cao = Y, đã căn giữa
  const s = new THREE.Shape(), x = -w / 2, y = -d / 2;
  s.moveTo(x + r, y); s.lineTo(x + w - r, y); s.quadraticCurveTo(x + w, y, x + w, y + r);
  s.lineTo(x + w, y + d - r); s.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
  s.lineTo(x + r, y + d); s.quadraticCurveTo(x, y + d, x, y + d - r);
  s.lineTo(x, y + r); s.quadraticCurveTo(x, y, x + r, y);
  const g = new THREE.ExtrudeGeometry(s, { depth: h, bevelEnabled: true, bevelThickness: bev, bevelSize: bev, bevelSegments: 3, curveSegments: 8 });
  g.rotateX(-Math.PI / 2); g.center();
  return g;
}
function heartGeo() {
  const s = new THREE.Shape();
  s.moveTo(.25, .25); s.bezierCurveTo(.25, .25, .2, 0, 0, 0); s.bezierCurveTo(-.3, 0, -.3, .35, -.3, .35);
  s.bezierCurveTo(-.3, .55, -.1, .77, .25, .95); s.bezierCurveTo(.6, .77, .8, .55, .8, .35);
  s.bezierCurveTo(.8, .35, .8, 0, .5, 0); s.bezierCurveTo(.35, 0, .25, .25, .25, .25);
  const g = new THREE.ExtrudeGeometry(s, { depth: .22, bevelEnabled: true, bevelThickness: .05, bevelSize: .05, bevelSegments: 3 });
  g.center(); g.scale(.55, .55, .55);
  return g;
}

const mat = (c) => new THREE.MeshStandardMaterial({
  color: c,
  roughness: 0.35,  /* Giảm độ nhám để trông bóng nhẹ như viên kẹo */
  metalness: 0.05
});


const M = {
  a: mat(0x82E0AA),    /* Xanh Mint tươi chủ đạo */
  b: mat(0xFFFDD0),    /* Trắng Kem xen kẽ */
  peach: mat(0xFFB7B2),/* Đào nhạt điểm xuyết */
  yellow: mat(0xFFE57F),/* Vàng gà con */
  goal: mat(0xFFB7B2), /* Ô đích màu đào ngọt */
  hole: mat(0x27AE60),
  ring: mat(0xFFFFFF),
  heart: mat(0xFFB7B2),
  light: mat(0xBDF2DA),      /* mặt trên mint nhạt (viền kem bên ngoài) */
  goalBase: mat(0xFFD54F),   /* ô đích: viền vàng */
  goalIn: mat(0x6FD3A0),
  holeIn: mat(0x5BD0A2)
};


const tileGeo = slab(.88, .88, .34, .17, .04);      // tile dày, bo tròn kiểu kẹo
tileGeo.translate(0, -(0.17 + 0.04), 0);            // mặt trên ở y = 0

const holeGeo = new THREE.CircleGeometry(.3, 32).rotateX(-Math.PI / 2);
const ringGeo = new THREE.RingGeometry(.3, .36, 32).rotateX(-Math.PI / 2);
/* ===== các kiểu tile: mint / kem viền mint nhạt / vàng / đào, kèm hoa văn nhỏ (cỏ, dấu chân chim, hoa cúc) ===== */
const insetGeo = slab(.62, .62, .004, .13, .004).translate(0, .006, 0);
const insetGoalGeo = slab(.70, .70, .004, .15, .004).translate(0, .006, 0);
const holeInGeo = new THREE.CircleGeometry(.22, 40).rotateX(-Math.PI / 2);
const hiGeo = new THREE.CircleGeometry(.055, 20).rotateX(-Math.PI / 2).scale(1.7, 1, 1);
const hiMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.9 });
const decalGeo = new THREE.PlaneGeometry(.52, .52).rotateX(-Math.PI / 2);

function decalTex(kind, col) {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"); g.translate(64, 64); g.lineCap = g.lineJoin = "round";
  if (kind === "grass") {                                  // cụm cỏ ba lá
    g.strokeStyle = col; g.lineWidth = 9;
    for (const [x, tilt, h] of [[-20, -1, 38], [0, 0, 50], [20, 1, 38]]) {
      g.beginPath(); g.moveTo(x * .7, 28); g.quadraticCurveTo(x * .7 + tilt * 4, 28 - h * .6, x * .7 + tilt * 22, 28 - h); g.stroke();
    }
  } else if (kind === "paw") {                             // dấu chân chim: ba ngón + gót
    g.strokeStyle = g.fillStyle = col; g.lineWidth = 11;
    for (const [tx, ty] of [[-27, -14], [0, -28], [27, -14]]) { g.beginPath(); g.moveTo(0, 14); g.lineTo(tx, ty); g.stroke(); }
    g.beginPath(); g.arc(0, 18, 9, 0, 7); g.fill();
  } else if (kind === "crack") {                           // vết nứt phân nhánh, có bóng và mảnh sứt
    // Lớp bóng lệch nhẹ làm vết nứt có chiều sâu trên mặt ô cam.
    const branches = [
      [[-50,-42],[-27,-25],[-14,-5],[-22,15],[-2,31],[10,49]],
      [[-14,-5],[7,-14],[18,-34],[34,-43]],
      [[-22,15],[-42,24],[-48,43]],
      [[-2,31],[20,25],[35,9],[49,5]],
      [[7,-14],[1,-34],[-5,-48]],
      [[20,25],[25,43]]
    ];
    g.strokeStyle = "rgba(104,48,20,.48)"; g.lineWidth = 10;
    for (const pts of branches) { g.beginPath(); pts.forEach(([x,y],i)=>(i?g.lineTo(x,y):g.moveTo(x,y))); g.stroke(); }
    g.strokeStyle = col; g.lineWidth = 5;
    for (const pts of branches) { g.beginPath(); pts.forEach(([x,y],i)=>(i?g.lineTo(x,y):g.moveTo(x,y))); g.stroke(); }
    // Những vết rạn nhỏ phụ và mảnh cạnh bị mẻ khiến tile trông giòn hơn.
    g.strokeStyle = "rgba(255,239,205,.9)"; g.lineWidth = 2.5;
    for (const pts of [[[-27,-25],[-39,-15]],[[18,-34],[29,-23]],[[-42,24],[-30,37]],[[35,9],[44,20]],[[1,-34],[13,-42]]]) {
      g.beginPath(); pts.forEach(([x,y],i)=>(i?g.lineTo(x,y):g.moveTo(x,y))); g.stroke();
    }
    g.fillStyle = "rgba(120,55,25,.55)";
    for (const [x,y,rot] of [[-49,-47,-.2],[48,-35,.3],[-47,47,.5],[47,42,-.4]]) {
      g.save(); g.translate(x,y); g.rotate(rot); g.beginPath(); g.moveTo(-5,-3); g.lineTo(4,-5); g.lineTo(5,4); g.closePath(); g.fill(); g.restore();
    }
  } else if (kind === "soft") {                            // nút nhẹ: vòng tròn + chấm
    g.strokeStyle = g.fillStyle = col; g.lineWidth = 10;
    g.beginPath(); g.arc(0, 0, 36, 0, 7); g.stroke(); g.beginPath(); g.arc(0, 0, 15, 0, 7); g.fill();
  } else if (kind === "heavy") {                           // nút nặng: ô vuông + dấu X
    g.strokeStyle = col; g.lineWidth = 10; g.strokeRect(-36, -36, 72, 72);
    g.lineWidth = 11; g.beginPath(); g.moveTo(-19, -19); g.lineTo(19, 19); g.moveTo(19, -19); g.lineTo(-19, 19); g.stroke();
  } else if (kind === "split") {                           // nút tách khối: hình thoi
    g.strokeStyle = g.fillStyle = col; g.lineWidth = 10;
    g.beginPath(); g.moveTo(0, -40); g.lineTo(40, 0); g.lineTo(0, 40); g.lineTo(-40, 0); g.closePath(); g.stroke();
    g.beginPath(); g.arc(0, 0, 11, 0, 7); g.fill();
  } else if (kind === "tele") {                            // điểm hạ cánh của khối tách
    g.strokeStyle = col; g.lineWidth = 8; g.beginPath(); g.arc(0, 0, 38, 0, 7); g.stroke(); g.beginPath(); g.arc(0, 0, 21, 0, 7); g.stroke();
  } else {                                                 // hoa cúc: 8 cánh trắng, nhụy cam
    for (let i = 0; i < 8; i++) {
      g.save(); g.rotate((i * Math.PI) / 4); g.beginPath(); g.ellipse(0, -27, 12, 21, 0, 0, 7);
      g.fillStyle = "#fff"; g.fill(); g.strokeStyle = "rgba(150,170,190,.35)"; g.lineWidth = 2; g.stroke(); g.restore();
    }
    g.beginPath(); g.arc(0, 0, 15, 0, 7); g.fillStyle = "#FFA826"; g.fill();
    g.beginPath(); g.arc(-4, -4, 6, 0, 7); g.fillStyle = "#FFD36B"; g.fill();
  }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
const decalCache = {};
function decalMat(kind, col) {
  const k = kind + col;
  return decalCache[k] || (decalCache[k] = new THREE.MeshBasicMaterial({
    map: decalTex(kind, col), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 }));
}
function hash2(r, c, sd) {
  let h = Math.imul(r + 1, 73856093) ^ Math.imul(c + 1, 19349663) ^ Math.imul(sd, 83492791);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function makeTile(r, c, ch, plain) {
  const m = new THREE.Mesh(tileGeo, M.a); m.receiveShadow = true;
  const add = (geo, mt, y) => { const o = new THREE.Mesh(geo, mt); o.position.y = y; m.add(o); return o; };
  if (ch === "G") {                                        // ô đích: viền vàng, lõi xanh, hố kính bóng
    m.material = M.goalBase; add(insetGoalGeo, M.goalIn, 0);
    add(holeGeo, M.hole, .016); add(holeInGeo, M.holeIn, .019);
    add(ringGeo, M.ring, .021); add(hiGeo, hiMat, .024).position.set(-.09, .024, -.09);
    return m;
  }
  const sd = idx * 7 + 3, h = hash2(r, c, sd), h2 = hash2(r, c, sd + 11);
  let type = h < 0.50 ? "mint" : h < 0.77 ? "light" : h < 0.89 ? "yellow" : "coral";
  if (ch === "S" || plain) type = "light";                          // ô xuất phát luôn là ô kem cho dễ thấy
  let y = .004, deco = null;
  if (type === "mint") { m.material = M.a; deco = h2 < .30 ? ["grass", "rgba(70,184,138,.9)"] : h2 < .50 ? ["paw", "rgba(70,184,138,.9)"] : null; }
  else if (type === "light") { m.material = M.b; add(insetGeo, M.light, 0); y = .016;
    deco = h2 < .45 ? ["daisy", ""] : h2 < .70 ? ["paw", "rgba(110,200,164,.95)"] : null; }
  else if (type === "yellow") { m.material = M.yellow; deco = h2 < .45 ? ["paw", "rgba(240,184,48,.95)"] : null; }
  else m.material = M.peach;
  if (deco && !plain) add(decalGeo, decalMat(deco[0], deco[1]), y);
  return m;
}
/* ---- ô đặc biệt: ô giòn, cầu, nút ---- */
M.frag = mat(0xFFB36B);
M.switchBase = mat(0x101116);
M.switchInset = mat(0x252832);
const BR_COLORS = [0x7EC8F0, 0xC8A2F0, 0xF59EC6, 0xF5C26B];
const brMats = BR_COLORS.map((c) => [mat(c), mat(new THREE.Color(c).lerp(new THREE.Color(0xffffff), .55))]);
const swGeo = new THREE.PlaneGeometry(.68, .68).rotateX(-Math.PI / 2);
function makeFragile() {
  const m = new THREE.Mesh(tileGeo, M.frag); m.receiveShadow = true; m.castShadow = true;
  // Mạng rạn đậm + đường sáng mảnh và các mẻ cạnh được vẽ trong decal để nhìn rõ từ góc camera.
  const d = new THREE.Mesh(decalGeo, decalMat("crack", "rgba(126,55,24,.95)"));
  d.position.y = .009; d.scale.set(1.06, 1, 1.06); d.renderOrder = 2; m.add(d);
  const warning = new THREE.Mesh(new THREE.PlaneGeometry(.38,.055).rotateX(-Math.PI/2), new THREE.MeshBasicMaterial({color:0xFFE1B3, transparent:true, opacity:.78, depthWrite:false}));
  warning.position.set(0,.010,0); warning.rotation.y = -.48; m.add(warning);
  m.userData.fragileVisual = true;
  return m;
}
function makeSwitchTile() {
  const m = new THREE.Mesh(tileGeo, M.switchBase); m.receiveShadow = true; m.castShadow = true;
  // Viền tối hơn một chút giúp ô đen vẫn có biên rõ trên nền.
  const rim = new THREE.Mesh(insetGeo, M.switchInset); rim.position.y = .004; m.add(rim);
  return m;
}
function makeBridge(k) {
  const m = new THREE.Mesh(tileGeo, brMats[k % 4][0]); m.receiveShadow = true;
  const i = new THREE.Mesh(insetGeo, brMats[k % 4][1]); i.position.y = .006; m.add(i);
  return m;
}
function addSwitchDecal(m, kind, col) {
  const switchColors = { soft: 0x55D6A6, heavy: 0xFF625D, split: 0xA879E8, tele: 0xF4A93A };
  const color = switchColors[kind] ?? 0xF4A93A;
  const radius = .235, baseY = .035;
  const dome = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2),
    new THREE.MeshStandardMaterial({color, roughness:.24, metalness:.04, emissive:color, emissiveIntensity:.12})
  );
  dome.position.set(0,baseY,0); dome.castShadow = true; dome.receiveShadow = true; m.add(dome);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(radius*.94,.025,8,32), new THREE.MeshStandardMaterial({color:0xFFFDF4, roughness:.3}));
  rim.rotation.x = Math.PI/2; rim.position.y = baseY+.008; rim.castShadow = true; m.add(rim);
  // Ký hiệu cũ được giữ lại nhưng thu nhỏ quanh chân nút.
  const d = new THREE.Mesh(swGeo, decalMat(kind, col)); d.position.y = .012; d.scale.set(.78,1,.78); d.renderOrder = 1; m.add(d);
}

/* bóng mềm của từng tile rơi xuống "đám mây" bên dưới: chồng lên nhau thành một vệt bóng liền */
const blobCv = document.createElement("canvas"); blobCv.width = blobCv.height = 64;
{ const g = blobCv.getContext("2d"), gr = g.createRadialGradient(32, 32, 4, 32, 32, 32);
  gr.addColorStop(0, "rgba(150,118,50,.85)"); gr.addColorStop(1, "rgba(150,118,50,0)"); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); }
const shadowGeo = new THREE.PlaneGeometry(1.5, 1.5).rotateX(-Math.PI / 2);
const shadowMat = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(blobCv), transparent: true, depthWrite: false, opacity: 0.24 });


const HL = .98, HW = .48;                 // nửa dài / nửa rộng của khối
const blk = new THREE.Group();
/* vàng gà con, bóng nhẹ; chấm bi kem vẽ thẳng trong shader theo toạ độ của khối nên không bị méo ở góc bo */
/* Vàng gà con pastel, tươi sáng & nổi bật trên nền Mint */
const blockMat = new THREE.MeshStandardMaterial({
  color: 0xFFE082,
  emissive: 0xFFC107,
  emissiveIntensity: 0.1,
  roughness: 0.35
});
blockMat.onBeforeCompile = (sh) => {
  sh.vertexShader = sh.vertexShader
    .replace("#include <common>", "#include <common>\nvarying vec3 vOP; varying vec3 vON;")
    .replace("#include <begin_vertex>", "#include <begin_vertex>\nvOP = position; vON = normal;");
  sh.fragmentShader = sh.fragmentShader
    .replace("#include <common>", `#include <common>
varying vec3 vOP; varying vec3 vON;
float h12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float dotsAt(vec2 uv, float seed){
  uv = uv * 2.9 + seed * 7.13;
  vec2 id = floor(uv), f = fract(uv);
  float h = h12(id + seed);
  vec2 c = vec2(.5) + (vec2(h12(id + 3.1), h12(id + 7.7)) - .5) * .30;
  float r = .20 + .03 * h12(id + 1.9);
  return step(.42, h) * (1. - smoothstep(r - .035, r, length(f - c)));
}`)
    .replace("#include <color_fragment>", `#include <color_fragment>
{
  vec3 an = abs(vON);
  float dm;
  if (an.y >= an.x && an.y >= an.z) dm = dotsAt(vOP.xz, 1.0 + sign(vON.y));
  else if (an.x >= an.z) dm = dotsAt(vOP.yz, 4.0 + sign(vON.x));
  else dm = dotsAt(vOP.xy, 7.0 + sign(vON.z));
  diffuseColor.rgb = mix(diffuseColor.rgb, vec3(1.0, 0.985, 0.90), dm);
}`);
};
const body = new THREE.Mesh(slab(.86, .86, 1.86, .2, .05), blockMat);
body.castShadow = true;
blk.add(body);

/* cành lá mint bo quanh khối: hai vòng dây leo ở 1/4 và 3/4 thân + cụm 3 lá nhỏ ở mỗi đầu */
(function addVines() {
  const TAU = Math.PI * 2, UPV = new THREE.Vector3(0, 1, 0);
  const vineMat = new THREE.MeshStandardMaterial({ color: 0x27AE60, roughness: 0.5 });
  const leafMat = new THREE.MeshStandardMaterial({
    color: 0xFFFFFF,
    roughness: 0.4,
    side: THREE.DoubleSide,
    emissive: 0x82E0AA,
    emissiveIntensity: 0.25
  });
  const leafShape = new THREE.Shape();                 // lá nhọn: gốc ở (0,0), ngọn ở (0,1)
  leafShape.moveTo(0, 0); leafShape.quadraticCurveTo(0.55, 0.28, 0, 1); leafShape.quadraticCurveTo(-0.55, 0.28, 0, 0);
  const leafGeo = new THREE.ShapeGeometry(leafShape, 8);
  const hw = 0.495, nExp = 4.2;                        // đường bao gần giống hình vuông bo góc của thân khối
  const ringPt = (phi, y) => {
    const c = Math.cos(phi), sn = Math.sin(phi);
    return new THREE.Vector3(Math.sign(c) * Math.pow(Math.abs(c), 2 / nExp) * hw, y + 0.028 * Math.sin(phi * 3),
      Math.sign(sn) * Math.pow(Math.abs(sn), 2 / nExp) * hw);
  };
  const MINTS = [0x7fe3c0, 0x9aebd0, 0x5fd6ae].map((h) => new THREE.Color(h));
  const items = [];
  for (const y of [-0.55, 0.55]) {
    const pts = [];
    for (let i = 0; i < 64; i++) pts.push(ringPt((i / 64) * TAU, y));
    blk.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), 128, 0.011, 6, true), vineMat));
    const L = 12;
    for (let i = 0; i < L; i++) {
      const phi = (i / L) * TAU, p = ringPt(phi, y), q = ringPt(phi + 0.02, y);
      const T = new THREE.Vector3(q.x - p.x, 0, q.z - p.z).normalize();
      const N = new THREE.Vector3(p.x, 0, p.z).normalize();
      const a = (i % 2 ? 1 : -1) * 0.75;               // lá chếch lên / xuống xen kẽ
      const D = T.clone().multiplyScalar(Math.cos(a)).addScaledVector(UPV, Math.sin(a)).normalize();
      items.push({ pos: p.clone().addScaledVector(N, 0.012), D, N, s: 0.15 + 0.015 * ((i * 7) % 3), c: i % 3 });
    }
  }
  const leaves = new THREE.InstancedMesh(leafGeo, leafMat, items.length);
  const dummy = new THREE.Object3D(), basis = new THREE.Matrix4(), xa = new THREE.Vector3();
  items.forEach((it, i) => {
    xa.crossVectors(it.D, it.N).normalize();           // lá nằm áp sát mặt khối: y = hướng lá, z = pháp tuyến mặt
    basis.makeBasis(xa, it.D, it.N);
    dummy.position.copy(it.pos); dummy.quaternion.setFromRotationMatrix(basis); dummy.scale.setScalar(it.s);
    dummy.updateMatrix(); leaves.setMatrixAt(i, dummy.matrix); leaves.setColorAt(i, MINTS[it.c]);
  });
  leaves.instanceMatrix.needsUpdate = true; leaves.instanceColor.needsUpdate = true;
  leaves.frustumCulled = false;
  blk.add(leaves);
  // hoa cúc: đầu khối (trên + dưới) và hai bông nhỏ ở thân
  const dm = decalMat("daisy", ""), capG = new THREE.PlaneGeometry(.36, .36), sideG = new THREE.PlaneGeometry(.30, .30);
  for (const sg of [1, -1]) { const f = new THREE.Mesh(capG, dm); f.rotation.x = -sg * Math.PI / 2; f.position.y = sg * 0.992; blk.add(f); }
  const f1 = new THREE.Mesh(sideG, dm); f1.position.set(0.1, -0.34, 0.489); blk.add(f1);
  const f2 = new THREE.Mesh(sideG, dm); f2.rotation.y = -Math.PI / 2; f2.position.set(-0.489, 0.30, -0.08); blk.add(f2);
})();
scene.add(blk);
const goalFlowerTex = (() => {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"); g.translate(64, 64); g.lineJoin = "round";
  for (let i = 0; i < 5; i++) {
    g.save(); g.rotate((i * 2 * Math.PI) / 5); g.beginPath(); g.arc(0, -30, 25, 0, 7);
    g.fillStyle = "#FF9A2E"; g.fill(); g.strokeStyle = "#EE7B12"; g.lineWidth = 4; g.stroke();
    g.beginPath(); g.arc(-4, -34, 9, 0, 7); g.fillStyle = "rgba(255,200,120,.7)"; g.fill(); g.restore();
  }
  g.beginPath(); g.arc(0, 0, 19, 0, 7); g.fillStyle = "#FFD23F"; g.fill(); g.strokeStyle = "#F5A91C"; g.lineWidth = 3; g.stroke();
  g.beginPath(); g.arc(-6, -6, 6, 0, 7); g.fillStyle = "rgba(255,255,255,.75)"; g.fill();
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
})();
const heart = new THREE.Sprite(new THREE.SpriteMaterial({ map: goalFlowerTex, transparent: true, depthWrite: false }));
heart.scale.set(0.95, 0.95, 1);
scene.add(heart);
const world = new THREE.Group();
scene.add(world);
/* hai khối lập phương nhỏ khi tách đôi: vàng (0) và hồng (1); khối đang điều khiển có vòng sáng + phát sáng */
const cubeGeo = slab(.86, .86, .86, .2, .05);
const ringCubeGeo = new THREE.RingGeometry(.54, .64, 32).rotateX(-Math.PI / 2);
const cubes = [0, 1].map((i) => {
  const m = new THREE.MeshStandardMaterial({ color: i ? 0xFFB7B2 : 0xFFE082, emissive: i ? 0xFF8A80 : 0xFFC107, emissiveIntensity: .1, roughness: .35 });
  const g = new THREE.Group(), b = new THREE.Mesh(cubeGeo, m); b.castShadow = true; g.add(b);
  const ring = new THREE.Mesh(ringCubeGeo, new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .95, side: THREE.DoubleSide }));
  ring.position.y = -.46; g.add(ring);
  g.userData = { mat: m, ring }; g.visible = false; scene.add(g); return g;
});
function setCubes(sp) {
  cubes.forEach((g, i) => {
    g.visible = !!sp;
    if (sp) { g.position.set(sp.cubes[i][1], .48, sp.cubes[i][0]); g.rotation.set(0, 0, 0); g.scale.set(1, 1, 1);
      g.userData.ring.visible = i === sp.active; g.userData.mat.emissiveIntensity = i === sp.active ? .45 : .05; }
  });
}
/* áp trạng thái do engine trả về (nguồn luật duy nhất) lên cảnh 3D */
function applyEngineState(st, fx) {
  const nb = new Set(st.bridges), wasSplit = splitMode;
  const changed = [...nb].filter((b) => !bridgeOpen.has(b)).concat([...bridgeOpen].filter((b) => !nb.has(b)));
  bridgeOpen = nb; es = st;
  for (const t of tileAt.values()) if (t.userData.bridge) t.userData.openT = nb.has(t.userData.bridge) ? 1 : 0;
  if (fx) for (const b of changed) for (const [r, c] of level.bridges[b]) burstWorld(c, .6, r, 10);
  splitMode = !!st.split;
  if (splitMode !== wasSplit) playEffectSound("split");
  $("swap").hidden = !splitMode;
  if (splitMode) {
    blk.visible = false; setCubes(st.split);
    if (!wasSplit) { cubePop = 0.0001; cubes.forEach((g) => g.scale.setScalar(.001)); if (fx) st.split.cubes.forEach(([r, c]) => burstWorld(c, .8, r, 24)); }
  } else {
    setCubes(null); blk.visible = true; state = [st.row, st.col, st.orient]; placeBlock(state);
    if (wasSplit) { pressCells(state); sq.a = .2; sq.v = 0; if (fx) burstWorld(st.col + (st.orient === "H" ? .5 : 0), .8, st.row + (st.orient === "V" ? .5 : 0), 24); }
  }
}

/* ---------- trạng thái ---------- */
let levels = [], idx = 0, level, state, moves = 0;
let es = null, splitMode = false, bridgeOpen = new Set(), loadSeq = 0, hop = null, cubeFall = null, cubePop = 1, rollDur = 0.22, playMs = 300;
const bridgeAt = new Map(), fragSet = new Set();
let status = "intro", introT = 0, anim = null, fallT = 0, fallY = 0, winT = 0, winY = 0;
const tiles = [];
let fall = null;
const tileAt = new Map(), pressed = new Map();   // ô sàn theo "r,c"; các ô đang bị khối đè (giá trị = độ lún)
const sq = { a: 0, v: 0 };                          // lò xo squishy của khối
const $ = (id) => document.getElementById(id);

const bgTracks = ["./audio/cute.mp3", "./audio/menu.mp3"];
const bgMusic = new Audio(bgTracks[Math.floor(Math.random() * bgTracks.length)]);
bgMusic.loop = true;
bgMusic.volume = 0.35;
let bgMusicStarted = false;
function startBgMusic() {
  if (save.settings.muteMusic || (bgMusicStarted && !bgMusic.paused)) return;
  bgMusicStarted = true;
  bgMusic.play().catch(() => { bgMusicStarted = false; });
}
document.addEventListener("pointerdown", startBgMusic);
document.addEventListener("keydown", startBgMusic);

const effectSounds = {
  loose: new Audio("./audio/loose.mp3"),
  broke: new Audio("./audio/broke-tiles.mp3"),
  win: new Audio("./audio/win.mp3"),
  split: new Audio("./audio/split.mp3"),
  click: new Audio("./audio/click.mp3")
};
Object.values(effectSounds).forEach((sound) => { sound.preload = "auto"; sound.volume = 0.8; });
function playEffectSound(kind) {
  if (save.settings.muteSounds) return;
  const sound = effectSounds[kind];
  sound.pause();
  sound.currentTime = 0;
  sound.play().catch(() => {});
}

function placeBlock(s) {
  const [r, c, o] = s;
  blk.rotation.set(0, 0, 0);
  if (o === "S") blk.position.set(c, HL, r);
  else if (o === "H") { blk.rotation.z = Math.PI / 2; blk.position.set(c + .5, HW, r); }
  else { blk.rotation.x = Math.PI / 2; blk.position.set(c, HW, r + .5); }
}

/* squishy: nén theo trục thẳng đứng của thế giới, đáy luôn chạm sàn, rồi nở ra từ từ */
function applySquish(a) {
  const o = state[2], sy = 1 - a, sx = 1 + a * 0.55;
  if (o === "S") { blk.scale.set(sx, sy, sx); blk.position.y = HL * sy; }
  else if (o === "H") { blk.scale.set(sy, sx, sx); blk.position.y = HW * sy; }
  else { blk.scale.set(sx, sx, sy); blk.position.y = HW * sy; }
  let sum = 0, k = 0;                                   // khối lún theo các ô đang đè
  for (const key of pressed.keys()) { const t = tileAt.get(key); if (t) { sum += t.userData.dy; k++; } }
  if (k) blk.position.y += sum / k;
}

// ---------- màn hình kết quả + đánh giá 5 sao ----------
let resultShown = false;
function ratingForMoves(used, optimal) {
  if (!Number.isFinite(optimal) || optimal <= 0) return 1;
  const ratio = used / optimal;
  if (ratio <= 1.00001) return 5;
  if (ratio <= 1.2) return 4;
  if (ratio <= 1.5) return 3;
  if (ratio <= 2.0) return 2;
  return 1;
}
function showResult() {
  if (resultShown) return;
  resultShown = true;
  const optimal = Number(level.optimal_moves);
  const stars = ratingForMoves(moves, optimal);
  $("resultLevel").textContent = `${level.name} · ${moves} nước đi`;
  $("resultStars").innerHTML = Array.from({length: 5}, (_, i) =>
    `<span class="${i < stars ? "earned" : ""}" aria-hidden="true">${i < stars ? "★" : "☆"}</span>`
  ).join("");
  $("resultStars").setAttribute("aria-label", `${stars} trên 5 sao`);
  const ratioText = Number.isFinite(optimal) && optimal > 0
    ? (moves <= optimal ? "Lời giải tối ưu! Tuyệt vời ✨" : `Tối ưu: ${optimal} nước · bạn dùng ${moves - optimal} nước nhiều hơn`)
    : "Hoàn thành màn chơi!";
  $("resultScore").textContent = `${stars}/5 sao · ${ratioText}`;
  $("resultNext").textContent = idx >= levels.length - 1 ? "Chơi màn đầu ↺" : "Màn tiếp theo →";
  $("resultNext").disabled = false;
  $("resultOverlay").hidden = false;
  $("solve").disabled = true;
  $("restart").disabled = true;
  $("menuBtn").disabled = true;
}
function hideResult() {
  $("resultOverlay").hidden = true;
  $("solve").disabled = false;
  $("restart").disabled = false;
  $("menuBtn").disabled = false;
}
$("resultNext").addEventListener("click", () => {
  stopSolverPlayback();
  hideResult();
  started = true;
  closeMenu();
  loadLevel(idx + 1);
});
$("resultReplay").addEventListener("click", () => {
  stopSolverPlayback();
  hideResult();
  started = true;
  closeMenu();
  loadLevel(idx);
});
$("resultMenu").addEventListener("click", () => {
  stopSolverPlayback();
  hideResult();
  openMenu();
});

function hud() {
  const st = save.settings;
  $("title").textContent = level.name;
  $("info").textContent = `Màn ${idx + 1}/${levels.length} · ${moves} nước đi` + (st.optimal ? ` · tối ưu ${level.optimal_moves ?? "?"}` : "") +
    (splitMode && es?.split ? ` · đang điều khiển khối ${es.split.active ? "hồng" : "vàng"}` : "");
  const last = idx === levels.length - 1;
  $("msg").textContent = status === "fell" ? "Oops, rớt rồi… thử lại nha ♡"
    : status === "won" ? `Hoàn thành trong ${moves} nước · chọn chơi lại hoặc đi tiếp nhé ♡`
      : st.hint ? (level.hint || "") : "";
}

function loadLevel(i) {
  loadSeq++; hop = null; cubeFall = null; cubePop = 1;
  stopSolverPlayback();
  // Reset all per-level completion state so the previous win cannot leak into the next level.
  resultShown = false;
  winT = 0;
  hideResult();
  idx = ((i % levels.length) + levels.length) % levels.length;
  level = makeLevel(levels[idx]);
  if (!inMenu) { save.progress = idx; save.maxLevel = Math.max(save.maxLevel, idx); persist(); }
  world.clear(); tiles.length = 0; tileAt.clear(); pressed.clear(); sq.a = sq.v = 0;
  if (fall) { scene.remove(fall.pivot); fall = null; }
  bridgeAt.clear(); fragSet.clear();
  const brIds = Object.keys(level.bridges || {}).sort();
  brIds.forEach((id) => level.bridges[id].forEach(([r, c]) => bridgeAt.set(r + "," + c, id)));
  (level.fragile || []).forEach(([r, c]) => fragSet.add(r + "," + c));
  bridgeOpen = new Set(level.bridges_initial_open || []);
  const swAt = new Map(), teleAt = new Set();
  (level.switches || []).forEach((sw) => {
    swAt.set(sw.pos[0] + "," + sw.pos[1], sw);
    (sw.teleport || []).forEach(([r, c]) => teleAt.add(r + "," + c));
  });
  const addShadow = (r, c) => {
    const sh = new THREE.Mesh(shadowGeo, shadowMat);        // bóng rơi xuống mây
    sh.position.set(c - 0.2, -1.1, r + 0.32); sh.renderOrder = -1;
    world.add(sh); return sh;
  };
  level.grid.forEach((row, r) => [...row].forEach((ch, c) => {
    if (ch === ".") return;
    const key = r + "," + c, sw = swAt.get(key);
    const m = fragSet.has(key) ? makeFragile() : sw ? makeSwitchTile() : makeTile(r, c, ch, !!teleAt.has(key));
    if (sw) {
      const tg = sw.targets || [], col = tg.length ? new THREE.Color(BR_COLORS[brIds.indexOf(tg[0]) % 4]).multiplyScalar(.72).getStyle() : "#F4A93A";
      addSwitchDecal(m, sw.type, col);
    } else if (teleAt.has(key)) addSwitchDecal(m, "tele", "#F4A93A");
    m.userData = { x: c, z: r, delay: (r + c) * 0.04, dy: 0, vy: 0 };
    tileAt.set(key, m);
    m.position.set(c, 5, r);
    world.add(m); tiles.push(m); addShadow(r, c);
  }));
  brIds.forEach((id, k) => level.bridges[id].forEach(([r, c]) => {
    const m = makeBridge(k), o = bridgeOpen.has(id) ? 1 : 0;
    m.userData = { x: c, z: r, delay: (r + c) * 0.04, dy: 0, vy: 0, bridge: id, o, openT: o, sh: addShadow(r, c) };
    m.scale.set(1, .06 + .94 * o, 1);
    tileAt.set(r + "," + c, m); m.position.set(c, 5, r);
    world.add(m); tiles.push(m);
  }));

  state = level.start; moves = 0; anim = null; introT = 0; status = "intro";
  es = { orient: "S", row: level.start[0], col: level.start[1], bridges: [...bridgeOpen], split: null };
  splitMode = false; setCubes(null); $("swap").hidden = true; $("stats").textContent = "";
  blk.visible = true; blk.scale.setScalar(0.001); heart.visible = true;
  scene.add(blk); placeBlock(state);
  document.documentElement.classList.remove("win");
  const cx = (level.cols - 1) / 2, cz = (level.rows - 1) / 2, big = Math.max(level.cols, level.rows);
  center.set(cx, .2, cz);
  sun.position.set(cx + 4, 11, cz + 6); sun.target.position.set(cx, 0, cz);
  const sc = sun.shadow.camera, e = big * 0.9 + 3;
  sc.left = -e; sc.right = e; sc.top = e; sc.bottom = -e; sc.updateProjectionMatrix();
  fit(); hud();
}

/* ---------- camera ---------- */
const center = new THREE.Vector3();
let az = 0, azT = 0, el = 0.95, R = 12, fitR = 12, zoomFactor = 1, dragging = false;
let solveQueue = [], solving = false, solveTimer = null;
function fit() {
  const w = innerWidth, h = innerHeight, asp = w / h;
  renderer.setSize(w, h); cam.aspect = asp; cam.updateProjectionMatrix();
  if (!level) return;
  const v = cam.fov * Math.PI / 180, hf = 2 * Math.atan(Math.tan(v / 2) * asp);
  const rad = Math.hypot(level.cols, level.rows) / 2 + 1.6;
  fitR = rad / Math.sin(Math.min(v, hf) / 2) * 0.72;
  R = fitR * zoomFactor;
}
addEventListener("resize", fit);
const changeZoom = (factor) => {
  zoomFactor = Math.min(2.5, Math.max(0.45, zoomFactor * factor));
  R = fitR * zoomFactor;
};
renderer.domElement.addEventListener("wheel", (e) => {
  e.preventDefault();
  changeZoom(Math.exp(e.deltaY * 0.001));
}, { passive: false });
renderer.domElement.addEventListener("pointerdown", (e) => { dragging = true; renderer.domElement.setPointerCapture(e.pointerId); });
renderer.domElement.addEventListener("pointermove", (e) => {
  if (!dragging) return;
  az -= e.movementX * 0.007; el = Math.min(1.4, Math.max(0.35, el + e.movementY * 0.005));
});
const endDrag = () => { if (dragging) { dragging = false; azT = Math.round(az / (Math.PI / 2)) * (Math.PI / 2); } };
renderer.domElement.addEventListener("pointerup", endDrag);
renderer.domElement.addEventListener("pointercancel", endDrag);
const turn = (n) => { azT = Math.round(azT / (Math.PI / 2)) * (Math.PI / 2) + n * Math.PI / 2; };

/* ---------- di chuyển ---------- */
const DIR_TO_ACTION = { UP: "U", DOWN: "D", LEFT: "L", RIGHT: "R" };
async function stepApi(action) {
  const r = await fetch("/api/step", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level_index: idx, state: es, action }) });
  const j = await r.json();
  if (!r.ok || !j.ok) throw new Error(j.error || "Lỗi /api/step");
  return j;
}
async function move(dir) {
  if (status !== "idle" || !level) return;
  if (splitMode) {                                   // bị khối kia chặn: không phải rơi, chỉ bỏ qua
    const sp = es.split, [r, c] = sp.cubes[sp.active], [dr, dc] = DIRV[dir], o = sp.cubes[1 - sp.active];
    if (r + dr === o[0] && c + dc === o[1]) return;
  }
  status = "wait"; const seq = loadSeq;
  let resp;
  try { resp = await stepApi(DIR_TO_ACTION[dir]); }
  catch (e) { if (seq === loadSeq) { status = "idle"; $("msg").textContent = `Mất kết nối server: ${e.message}`; } return; }
  if (seq !== loadSeq) return;
  if (splitMode) startHop(dir, resp); else startRoll(dir, resp);
}
async function swapCube() {
  if (status !== "idle" || !splitMode) return;
  status = "wait"; const seq = loadSeq;
  try {
    const resp = await stepApi("SWAP");
    if (seq !== loadSeq) return;
    moves++; applyEngineState(resp.state, false); status = "idle"; hud();
  } catch (e) { if (seq === loadSeq) status = "idle"; }
}
function startHop(dir, resp) {
  const sp = es.split, a = sp.active, [r, c] = sp.cubes[a], [dr, dc] = DIRV[dir];
  pressed.clear(); moves++;
  hop = { g: cubes[a], x0: c, z0: r, dx: dc, dz: dr, t: 0, resp };
  status = "rolling";
}
function finishHop() {
  const { g, resp, dx, dz } = hop; hop = null;
  if (!resp.legal) { playEffectSound("loose"); cubeFall = { g, dx, dz, x0: g.position.x, z0: g.position.z }; status = "fell"; fallT = 0; hud(); return; }
  applyEngineState(resp.state, true);
  status = "idle"; hud();
}
function startRoll(dir, resp) {
  const n = roll(state, dir);
  const legal = resp.legal;
  const cs = cellsOf(state);
  const rs = cs.map((p) => p[0]), cc = cs.map((p) => p[1]);
  const minR = Math.min(...rs), maxR = Math.max(...rs), minC = Math.min(...cc), maxC = Math.max(...cc);
  let px = (minC + maxC) / 2, pz = (minR + maxR) / 2, axis, ang;
  if (dir === "RIGHT") { px = maxC + .5; axis = "z"; ang = -Math.PI / 2; }
  if (dir === "LEFT") { px = minC - .5; axis = "z"; ang = Math.PI / 2; }
  if (dir === "DOWN") { pz = maxR + .5; axis = "x"; ang = Math.PI / 2; }
  if (dir === "UP") { pz = minR - .5; axis = "x"; ang = -Math.PI / 2; }
  const pivot = new THREE.Group();
  pivot.position.set(px, 0, pz);
  pressed.clear(); sq.a = sq.v = 0; blk.scale.set(1, 1, 1); placeBlock(state);
  scene.add(pivot); pivot.attach(blk);
  moves++;
  anim = { t: 0, dur: rollDur, pivot, axis, ang, n, legal, dir, resp };
  status = "rolling";
}
const DIRV = { UP: [-1, 0], DOWN: [1, 0], LEFT: [0, -1], RIGHT: [0, 1] };   // [dr, dc]
function pressCells(st) {
  const depth = st[2] === "S" ? 0.1 : 0.055;
  for (const [r, c] of cellsOf(st)) {
    const t = tileAt.get(r + "," + c);
    if (t) { pressed.set(r + "," + c, depth); t.userData.vy -= 1.4; }   // chạm xuống là lún một nhịp
  }
}
function startFall(pivot, axis, sign, base, dr, dc, alpha, maxAng, sound = "loose") {
  fall = { pivot, axis, sign, base, alpha, maxAng, x0: pivot.position.x, z0: pivot.position.z, dr, dc };
  playEffectSound(sound);
  status = "fell"; fallT = 0;
}
function finishRoll() {
  const { pivot, n, legal, axis, ang, dir, resp } = anim;
  anim = null; state = n;
  if (!legal) {
    const cs = cellsOf(n);
    const sup = cs.filter(([r, c]) => level.walk(r, c)), gone = cs.filter(([r, c]) => !level.walk(r, c));
    if (!sup.length) {
      // lăn hẳn ra ngoài mép: khối tiếp tục lật quanh mép vừa rời đi, trôi ra xa rồi rơi
      startFall(pivot, axis, Math.sign(ang), ang, ...DIRV[dir], 5, 1.0);
    } else if (!gone.length) {
      // đủ chỗ đứng nhưng luật không cho (ô giòn vỡ / cầu sập): khối rơi thẳng xuống, ô giòn vỡ theo
      const breaks = n[2] === "S" ? cs.map(([r, c]) => tileAt.get(r + "," + c)).filter((t) => t && fragSet.has(t.userData.z + "," + t.userData.x)) : [];
      breaks.forEach((t) => { t.userData.broken = true; });
      startFall(pivot, axis, 0, ang, 0, 0, 0, 0, breaks.length ? "broke" : "loose");
    } else {
      // nằm vắt qua mép: đổ về phía ô trống, quay quanh đường biên giữa ô có sàn và ô trống
      scene.add(blk); scene.remove(pivot); placeBlock(n);
      const tdr = gone[0][0] - sup[0][0], tdc = gone[0][1] - sup[0][1];
      const np = new THREE.Group();
      np.position.set(sup[0][1] + tdc * 0.5, 0, sup[0][0] + tdr * 0.5);
      scene.add(np); np.attach(blk);
      startFall(np, tdc !== 0 ? "z" : "x", tdc !== 0 ? (tdc > 0 ? -1 : 1) : (tdr > 0 ? 1 : -1), 0, tdr, tdc, 7, 1.75);
    }
    hud(); return;
  }
  scene.add(blk); scene.remove(pivot); placeBlock(n);
  applyEngineState(resp.state, true);
  if (resp.status === "won") {
    playEffectSound("win");
    status = "won"; winT = 0; winY = blk.position.y; heart.visible = false; document.documentElement.classList.add("win");
    const b = save.best[level.name]; if (b == null || moves < b) save.best[level.name] = moves;
    save.progress = idx; persist();
    burstWorld(level.goal[1], 1.0, level.goal[0], 70);
  } else {
    status = "idle";
    if (!splitMode) { pressCells(n); sq.a = n[2] === "S" ? 0.13 : 0.2; sq.v = 0; }   // đáp xuống: nén rồi nở từ từ
  }
  hud();
}

// ---------- solver integration (Python engine API) ----------
const ACTION_TO_DIR = { U: "UP", D: "DOWN", L: "LEFT", R: "RIGHT" };
function stopSolverPlayback() {
  solving = false;
  solveQueue = []; rollDur = 0.22; playMs = 300;
  if (solveTimer !== null) { clearTimeout(solveTimer); solveTimer = null; }
  const button = $("solve");
  if (button) { button.disabled = false; button.textContent = `Solve · ${$("solverAlgorithm")?.value.toUpperCase() || "BFS"}`; }
}
function playNextSolverMove() {
  if (!solving) return;
  if (!solveQueue.length) {
    solving = false; rollDur = 0.22; playMs = 300;
    $("solve").disabled = false;
    $("solve").textContent = `Solve · ${$("solverAlgorithm").value.toUpperCase()}`;
    $("msg").textContent = "Đã phát xong lời giải ♡";
    return;
  }
  if (status === "won" || status === "fell") {
    stopSolverPlayback();
    return;
  }
  if (status !== "idle") {
    solveTimer = setTimeout(playNextSolverMove, 100);
    return;
  }
  const action = solveQueue.shift();
  if (action === "SWAP") { swapCube(); solveTimer = setTimeout(playNextSolverMove, playMs); return; }
  const dir = ACTION_TO_DIR[action];
  if (!dir) {
    stopSolverPlayback();
    $("msg").textContent = `GUI chưa hỗ trợ action ${action} (ví dụ SWAP của cơ chế split).`;
    return;
  }
  move(dir);
  solveTimer = setTimeout(playNextSolverMove, playMs);
}
async function requestSolution() {
  if (solving || !level || inMenu) return;
  if (status === "rolling" || status === "wait" || status === "fell" || status === "won") {
    $("msg").textContent = "Hãy chơi lại màn trước khi chạy Solve.";
    return;
  }
  const button = $("solve");
  button.disabled = true; button.textContent = "Đang tìm…";
  const algorithm = $("solverAlgorithm").value;
  $("msg").textContent = `Đang tìm đường đi bằng ${algorithm.toUpperCase()}…`;
  try {
    const response = await fetch("/api/solve", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level_index: idx, algorithm, cost: $("solverCost").value })
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || "Không thể giải màn này");
    if (!result.solvable || !Array.isArray(result.path)) {
      button.disabled = false; button.textContent = `Solve · ${$("solverAlgorithm").value.toUpperCase()}`;
      $("msg").textContent = "Solver không tìm thấy lời giải cho màn này.";
      return;
    }
    // Restart the visual board so playback starts from the engine's initial state.
    loadLevel(idx);
    solveQueue = result.path.slice(); solving = true;
    const fast = result.path.length > 80; rollDur = fast ? 0.11 : 0.22; playMs = fast ? 140 : 300;
    button.disabled = true; button.textContent = `Đang giải ${algorithm.toUpperCase()}…`;
    $("msg").textContent = `${algorithm.toUpperCase()} tìm được lời giải ${result.length} nước.`;
    $("stats").textContent = `cost ${result.cost} · mở rộng ${result.expanded} nút · ${result.time_ms} ms · ${result.memory_kb} KB`;
    playNextSolverMove();
  } catch (error) {
    button.disabled = false; button.textContent = `Solve · ${$("solverAlgorithm").value.toUpperCase()}`;
    $("msg").textContent = `Không gọi được solver: ${error.message}`;
  }
}
$("solve").addEventListener("click", requestSolution);
$("solverAlgorithm").addEventListener("change", () => { if (!solving) $("solve").textContent = `Solve · ${$("solverAlgorithm").value.toUpperCase()}`; });

addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (inMenu) { if (!$("pMain").hidden) { if (started) closeMenu(); } else showPanel("pMain"); }
    else openMenu();
    return;
  }
  if (resultShown && (e.key === "Enter" || e.key === "NumpadEnter")) {
    e.preventDefault();
    if (!e.repeat) $("resultNext").click();
    return;
  }
  if (inMenu || resultShown) return;
  const map = { ArrowUp: 0, ArrowRight: 1, ArrowDown: 2, ArrowLeft: 3, w: 0, d: 1, s: 2, a: 3, W: 0, D: 1, S: 2, A: 3 };
  if (e.key in map) {
    e.preventDefault();
    const k = Math.round(azT / (Math.PI / 2));
    move(LIST[(((map[e.key] - k) % 4) + 4) % 4]);
  } else if (e.key === " " || e.key === "f" || e.key === "F") {
    e.preventDefault(); swapCube();
  } else if (e.key === "r" || e.key === "R") loadLevel(idx);
  else if (e.key === "n" || e.key === "N" || e.key === "]") loadLevel(idx + 1);
  else if (e.key === "[") loadLevel(idx - 1);
  else if (e.key === "q" || e.key === "Q") turn(-1);
  else if (e.key === "e" || e.key === "E") turn(1);
  else if (e.key === "+" || e.key === "=") { e.preventDefault(); changeZoom(0.85); }
  else if (e.key === "-" || e.key === "_") { e.preventDefault(); changeZoom(1.18); }
});
$("menuBtn").onclick = () => openMenu();
$("restart").onclick = () => loadLevel(idx);
$("swap").onclick = () => swapCube();
$("rl").onclick = () => turn(-1);
$("rr").onclick = () => turn(1);

// Âm click dùng chung cho mọi button, kể cả các button được tạo sau khi tải màn.
effectSounds.click.preload = "auto";
effectSounds.click.volume = 0.65;
document.addEventListener("click", (e) => {
  if (!e.target.closest || !e.target.closest("button:not(:disabled)") || save.settings.muteSounds) return;
  const sound = effectSounds.click;
  sound.pause(); sound.currentTime = 0;
  sound.play().catch(() => {});
});

function openGuide() { $("guideOverlay").hidden = false; }
function closeGuide() { $("guideOverlay").hidden = true; }
$("guideBtn").onclick = openGuide;
$("mGuide").onclick = openGuide;
$("guideClose").onclick = closeGuide;
$("guideOverlay").addEventListener("click", (e) => { if (e.target === $("guideOverlay")) closeGuide(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("guideOverlay").hidden) closeGuide(); });

/* ---------- lưu trữ (localStorage) + menu khởi đầu ---------- */
const KEY = "bloxorz.v1";
const DEF = { hint: true, optimal: true, auto: true, snow: true, fx: true, muteMusic: false, muteSounds: false };
function readSave() {
  try {
    const x = JSON.parse(localStorage.getItem(KEY) || "{}");
    return { progress: x.progress ?? null, maxLevel: x.maxLevel ?? 0, best: x.best || {}, settings: { ...DEF, ...(x.settings || {}) } };
  } catch { return { progress: null, maxLevel: 0, best: {}, settings: { ...DEF } }; }
}
let save = readSave();
// Thử phát nhạc ngay khi mở trang; nếu trình duyệt chặn autoplay, các sự kiện
// pointerdown/keydown phía trên sẽ phát lại khi người chơi tương tác.
startBgMusic();
function persist() { try { localStorage.setItem(KEY, JSON.stringify(save)); } catch { /* bỏ qua */ } }
let inMenu = true, started = false;
// Hướng dẫn xuất hiện tự động khi mở game lần đầu trong trang này.
openGuide();

const mk = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
function showPanel(id) {
  ["pMain", "pLevels", "pAch", "pSet"].forEach((p) => ($(p).hidden = p !== id));
  if (id === "pLevels") renderLevels();
  if (id === "pAch") renderAch();
  if (id === "pSet") renderSet();
}
function refreshMenu() {
  const has = started || save.progress != null;
  const i = started ? idx : save.progress;
  $("mCont").disabled = !has;
  $("mCont").textContent = has && levels[i] ? `Tiếp tục màn cũ · Màn ${i + 1}` : "Tiếp tục màn cũ";
}
function openMenu() { inMenu = true; $("menu").classList.remove("off"); showPanel("pMain"); refreshMenu(); }
function closeMenu() { inMenu = false; $("menu").classList.add("off"); azT = Math.round(az / (Math.PI / 2)) * (Math.PI / 2); }

function renderLevels() {
  const box = $("levelList"); box.replaceChildren();
  const completed = levels.filter((l) => save.best[l.name] != null).length;
  $("levelSum").textContent = `Đã hoàn thành ${completed}/${levels.length} màn · chọn bất kỳ màn nào để chơi lại`;
  levels.forEach((l, i) => {
    const best = save.best[l.name];
    const stars = best == null ? 0 : ratingForMoves(best, Number(l.optimal_moves));
    const card = mk("button", `level-card${best != null ? " completed" : ""}${i === idx ? " current" : ""}`);
    card.type = "button";
    const name = mk("span", "level-name", `${String(i + 1).padStart(2,"0")} · ${l.name}`);
    const starLine = mk("span", "level-stars");
    starLine.innerHTML = Array.from({length:5},(_,n)=>`<span class="${n < stars ? "earned" : ""}">${n < stars ? "★" : "☆"}</span>`).join("");
    const stateText = mk("span", "level-state", best == null ? "Chưa hoàn thành" : `Kỷ lục: ${best} nước`);
    card.append(name, starLine, stateText);
    card.onclick = () => {
      started = true; closeMenu(); loadLevel(i);
    };
    box.append(card);
  });
}

function renderAch() {
  const box = $("achList"); box.replaceChildren();
  const done = levels.filter((l) => save.best[l.name] != null);
  const perfect = done.filter((l) => save.best[l.name] <= l.optimal_moves).length;
  $("achSum").textContent = `Đã qua ${done.length}/${levels.length} màn · màn cao nhất: ${Math.min(save.maxLevel, levels.length - 1) + 1} · tối ưu ${perfect} màn`;
  levels.forEach((l, i) => {
    const b = save.best[l.name], row = mk("div", "row");
    row.append(mk("span", "nm", `${i + 1}. ${l.name}`),
      mk("span", "sc", b == null ? "chưa qua" : b <= l.optimal_moves ? `${b} nước ⭐` : `${b} nước (tối ưu ${l.optimal_moves})`));
    box.append(row);
  });
}
const SETS = [["hint", "Hiện gợi ý ở mỗi màn"], ["optimal", "Hiện số nước tối ưu"], ["auto", "Tự động qua màn khi thắng"],
["snow", "Hiệu ứng tuyết rơi"], ["fx", "Hiệu ứng lấp lánh theo chuột"], ["muteMusic", "Tắt nhạc nền"], ["muteSounds", "Tắt âm thanh hiệu ứng"]];
function renderSet() {
  const box = $("setList"); box.replaceChildren();
  for (const [k, label] of SETS) {
    const row = mk("label", "row"), cb = mk("input");
    cb.type = "checkbox"; cb.checked = save.settings[k];
    cb.onchange = () => {
      save.settings[k] = cb.checked;
      persist();
      if (k === "muteMusic") {
        if (cb.checked) bgMusic.pause();
        else startBgMusic();
      }
      if (k === "muteSounds" && cb.checked) Object.values(effectSounds).forEach((sound) => { sound.pause(); sound.currentTime = 0; });
      applyFx();
      if (level) hud();
    };
    row.append(mk("span", "nm", label), cb); box.append(row);
  }
}

$("mNew").onclick = () => {
  if ((save.progress ?? 0) > 0 && !confirm("Bắt đầu lại từ màn 1 nha? Thành tựu của bạn vẫn được giữ ♡")) return;
  started = true; closeMenu(); loadLevel(0);
};
$("mCont").onclick = () => {
  if (started) {
    // Nếu mở menu sau khi thắng/rớt, "Tiếp tục" phải khởi tạo lại màn
    // thay vì đóng menu nhưng giữ status won/fell khiến điều khiển bị khóa.
    const mustRestart = status === "won" || status === "fell";
    closeMenu();
    if (mustRestart) loadLevel(idx);
    return;
  }
  started = true; closeMenu(); loadLevel(save.progress ?? 0);
};
$("mLevels").onclick = () => showPanel("pLevels");
$("mAch").onclick = () => showPanel("pAch");
$("mSet").onclick = () => showPanel("pSet");
document.querySelectorAll(".back").forEach((b) => (b.onclick = () => showPanel("pMain")));
$("resetAll").onclick = () => {
  if (!confirm("Xóa toàn bộ tiến độ và thành tựu?")) return;
  save = { progress: null, maxLevel: 0, best: {}, settings: { ...save.settings } };
  started = false; persist(); refreshMenu(); showPanel("pMain");
};

/* ---------- hiệu ứng: tuyết rơi + lấp lánh theo chuột ---------- */
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
const fxTime = { value: 0 };
const mouseW = { value: new THREE.Vector3(9999, 0, 9999) };     // con trỏ trên mặt phẳng bàn chơi
const ptr = { ndcX: 0, ndcY: 0, sx: 0, sy: 0, live: false };

function spriteTex(draw) {
  const c = document.createElement("canvas"); c.width = c.height = 64;
  draw(c.getContext("2d")); return new THREE.CanvasTexture(c);
}
const flakeTex = spriteTex((g) => {                              // bông tuyết: lõi trắng, viền hồng mờ
  const gr = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.36, "rgba(255,255,255,.95)");
  gr.addColorStop(0.62, "rgba(255,238,170,.6)"); gr.addColorStop(1, "rgba(255,228,120,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 64, 64);
});
const sparkTex = spriteTex((g) => {                              // ngôi sao 4 cánh
  g.translate(32, 32);
  const gr = g.createRadialGradient(0, 0, 0, 0, 0, 30);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.25, "rgba(255,238,140,.85)"); gr.addColorStop(1, "rgba(255,226,90,0)");
  g.fillStyle = gr; g.fillRect(-32, -32, 64, 64);
  g.beginPath(); g.moveTo(0, -29); g.quadraticCurveTo(2.5, -2.5, 29, 0); g.quadraticCurveTo(2.5, 2.5, 0, 29);
  g.quadraticCurveTo(-2.5, 2.5, -29, 0); g.quadraticCurveTo(-2.5, -2.5, 0, -29);
  g.strokeStyle = "rgba(240,190,30,.95)"; g.lineWidth = 2; g.stroke(); g.fillStyle = "#fff"; g.fill();
});

/* tuyết: mọi chuyển động chạy trong vertex shader theo uTime, CPU chỉ ghi vài uniform mỗi frame */
const SNOW_N = calm ? 220 : 520;
const snowGeo = new THREE.BufferGeometry();
{
  const pos = new Float32Array(SNOW_N * 3), seed = new Float32Array(SNOW_N * 4);
  for (let i = 0; i < SNOW_N; i++) {
    pos.set([Math.random(), Math.random(), Math.random()], i * 3);
    seed.set([Math.random() * 6.283, 0.55 + Math.random() * 0.9, 0.4 + Math.random() * 1.2, 0.5 + Math.pow(Math.random(), 2.2) * 1.1], i * 4);
  }
  snowGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  snowGeo.setAttribute("seed", new THREE.BufferAttribute(seed, 4));
}
const snowMat = new THREE.ShaderMaterial({
  uniforms: {
    uTime: fxTime, uMap: { value: flakeTex }, uCenter: { value: new THREE.Vector3() }, uSpan: { value: 12 },
    uMouse: mouseW, uScale: { value: 400 }, uSize: { value: 0.11 }
  },
  transparent: true, depthWrite: false,
  vertexShader: `
    attribute vec4 seed;
    uniform float uTime, uSpan, uScale, uSize;
    uniform vec3 uCenter, uMouse;
    varying float vA;
    void main(){
      float ph = seed.x, sp = seed.y, sw = seed.z;
      float H = 15.0;
      float fall = mod(position.y * H - uTime * sp * 0.9, H);
      vec3 p = vec3((position.x - 0.5) * uSpan * 2.0, fall - 1.5, (position.z - 0.5) * uSpan * 2.0);
      p.x += sin(uTime * 0.6 * sp + ph) * 0.45 * sw + sin(uTime * 1.3 + ph * 2.0) * 0.12;
      p.z += cos(uTime * 0.5 * sp + ph) * 0.45 * sw;
      p += uCenter;
      vec3 d = p - uMouse;
      float infl = smoothstep(2.4, 0.0, length(vec3(d.x, d.y * 0.45, d.z)));
      infl *= infl;
      p.xz += normalize(d.xz + vec2(1e-4)) * infl * 1.6;
      p.y += infl * 0.5;
      vec4 mv = modelViewMatrix * vec4(p, 1.0);
      gl_PointSize = uSize * seed.w * uScale / max(-mv.z, 0.5);
      float edge = smoothstep(0.0, 1.6, fall) * (1.0 - smoothstep(H - 2.0, H, fall));
      float near = smoothstep(1.5, 5.0, -mv.z);
      vA = edge * near * (0.60 + 0.30 * sin(uTime * (0.8 + sp) + ph * 3.0));
      gl_Position = projectionMatrix * mv;
    }`,
  fragmentShader: `
    precision highp float;
    uniform sampler2D uMap; varying float vA;
    void main(){ vec4 t = texture2D(uMap, gl_PointCoord); gl_FragColor = vec4(t.rgb, t.a * vA); }`,
});
const snow = new THREE.Points(snowGeo, snowMat);
snow.frustumCulled = false; snow.renderOrder = 5; scene.add(snow);

/* lấp lánh: vòng đệm hạt, mỗi hạt tự bay theo thời gian sinh ra (aBirth) */
const SP_N = 360, SP_LIFE = 1.3;
const spPos = new Float32Array(SP_N * 3), spVel = new Float32Array(SP_N * 3), spBirth = new Float32Array(SP_N).fill(-999), spRnd = new Float32Array(SP_N * 2);
const spGeo = new THREE.BufferGeometry();
spGeo.setAttribute("position", new THREE.BufferAttribute(spPos, 3));
spGeo.setAttribute("aVel", new THREE.BufferAttribute(spVel, 3));
spGeo.setAttribute("aBirth", new THREE.BufferAttribute(spBirth, 1));
spGeo.setAttribute("aRnd", new THREE.BufferAttribute(spRnd, 2));
const sparkMat = new THREE.ShaderMaterial({
  uniforms: { uTime: fxTime, uMap: { value: sparkTex }, uSize: { value: 0.24 }, uScale: { value: 400 }, uLife: { value: SP_LIFE } },
  transparent: true, depthWrite: false, depthTest: false,
  vertexShader: `
    attribute vec3 aVel; attribute float aBirth; attribute vec2 aRnd;
    uniform float uTime, uSize, uScale, uLife;
    varying float vA; varying float vTint;
    void main(){
      float age = uTime - aBirth;
      if (age < 0.0 || age > uLife) { vA = 0.0; vTint = 0.0; gl_PointSize = 0.0; gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
      float u = age / uLife;
      vec3 p = position + aVel * age * (1.0 - 0.5 * u);
      p.y += 0.55 * age;
      p.x += sin(aRnd.y * 6.28 + age * 3.0) * 0.18 * u;
      vec4 mv = modelViewMatrix * vec4(p, 1.0);
      float tw = 0.7 + 0.3 * sin(age * 18.0 + aRnd.y * 20.0);
      gl_PointSize = uSize * aRnd.x * uScale / max(-mv.z, 0.5) * (0.35 + 0.65 * (1.0 - u)) * tw;
      vA = smoothstep(0.0, 0.08, u) * (1.0 - smoothstep(0.4, 1.0, u));
      vTint = aRnd.y;
      gl_Position = projectionMatrix * mv;
    }`,
  fragmentShader: `
    precision highp float;
    uniform sampler2D uMap; varying float vA; varying float vTint;
    void main(){
      vec4 t = texture2D(uMap, gl_PointCoord);
      vec3 tint = mix(vec3(1.0, 0.86, 0.28), vec3(0.50, 0.90, 0.76), step(0.5, vTint));
      vec3 c = mix(t.rgb, tint, 0.55);
      gl_FragColor = vec4(c, t.a * vA);
    }`,
});
const sparks = new THREE.Points(spGeo, sparkMat);
sparks.frustumCulled = false; sparks.renderOrder = 6; scene.add(sparks);

let spHead = 0, spDirty = false;
function spawn(p, k) {
  const i = spHead, o = i * 3; spHead = (spHead + 1) % SP_N;
  spPos[o] = p.x + (Math.random() - .5) * .25 * k; spPos[o + 1] = p.y + (Math.random() - .5) * .2 * k; spPos[o + 2] = p.z + (Math.random() - .5) * .25 * k;
  spVel[o] = (Math.random() - .5) * .9 * k; spVel[o + 1] = (.2 + Math.random() * .9) * k; spVel[o + 2] = (Math.random() - .5) * .9 * k;
  spBirth[i] = fxTime.value; spRnd[i * 2] = .6 + Math.random() * .9; spRnd[i * 2 + 1] = Math.random();
  spDirty = true;
}
function flushSparks() {
  if (!spDirty) return;
  for (const k of ["position", "aVel", "aBirth", "aRnd"]) spGeo.attributes[k].needsUpdate = true;
  spDirty = false;
}

const fxRay = new THREE.Raycaster(), fxNdc = new THREE.Vector2(), hitP = new THREE.Vector3(), lastP = new THREE.Vector3(9999, 0, 0), tmpP = new THREE.Vector3();
const sparkPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -0.8);

function burstAt(cx, cy, n) {                                     // nổ lấp lánh tại vị trí con trỏ trên màn hình
  if (!save.settings.fx || calm || !level) return;
  cam.updateMatrixWorld();
  fxNdc.set((cx / innerWidth) * 2 - 1, -(cy / innerHeight) * 2 + 1); fxRay.setFromCamera(fxNdc, cam);
  if (!fxRay.ray.intersectPlane(sparkPlane, hitP)) return;
  for (let i = 0; i < n; i++) spawn(hitP, 2.2);
  flushSparks();
}
function burstWorld(x, y, z, n) {                                 // nổ lấp lánh tại một điểm trong thế giới 3D
  if (!save.settings.fx || calm) return;
  hitP.set(x, y, z);
  for (let i = 0; i < n; i++) spawn(hitP, 3);
  flushSparks();
}
function applyFx() { snow.visible = save.settings.snow; sparks.visible = save.settings.fx; }

function fxUpdate(dt) {
  if (!calm) fxTime.value += dt;
  shadowMat.opacity = 0.24 * (status === "intro" ? clamp01((introT - 0.35) / 0.6) : 1);
  updateDecor();
  const ease = Math.min(1, dt * 3.5);
  ptr.sx += ((ptr.live ? ptr.ndcX : 0) - ptr.sx) * ease;
  ptr.sy += ((ptr.live ? ptr.ndcY : 0) - ptr.sy) * ease;
  snowMat.uniforms.uCenter.value.copy(center);
  snowMat.uniforms.uSpan.value = Math.max(level.cols, level.rows) * 0.8 + 7;
  snowMat.uniforms.uScale.value = sparkMat.uniforms.uScale.value =
    renderer.domElement.height / 2 / Math.tan(cam.fov * Math.PI / 360);

  if (!(ptr.live && save.settings.fx && !calm)) { mouseW.value.set(9999, 0, 9999); lastP.x = 9999; return; }
  cam.updateMatrixWorld();
  fxNdc.set(ptr.ndcX, ptr.ndcY); fxRay.setFromCamera(fxNdc, cam);
  if (!fxRay.ray.intersectPlane(sparkPlane, hitP)) return;
  if (mouseW.value.x > 9000) mouseW.value.copy(hitP); else mouseW.value.lerp(hitP, 1 - Math.pow(0.0004, dt));
  if (lastP.x > 9000) { lastP.copy(hitP); return; }
  const d = hitP.distanceTo(lastP), n = Math.min(8, Math.floor(d / 0.3));
  for (let k = 1; k <= n; k++) { tmpP.lerpVectors(lastP, hitP, k / n); spawn(tmpP, 1); }
  if (n > 0) lastP.copy(hitP);
  flushSparks();
}

const menuCard = document.querySelector("#menu .card");
addEventListener("pointermove", (e) => {
  if (e.pointerType === "touch") return;
  ptr.ndcX = (e.clientX / innerWidth) * 2 - 1; ptr.ndcY = -(e.clientY / innerHeight) * 2 + 1; ptr.live = true;
  if (inMenu && !calm) menuCard.style.transform = `perspective(900px) rotateY(${ptr.ndcX * 4}deg) rotateX(${-ptr.ndcY * 3}deg)`;
}, { passive: true });
document.documentElement.addEventListener("pointerleave", () => { ptr.live = false; });
// nút nào cũng bắn lấp lánh khi rê vào / bấm
document.addEventListener("pointerover", (e) => {
  const b = e.target.closest && e.target.closest("button:not(:disabled)");
  if (b && !b.contains(e.relatedTarget)) burstAt(e.clientX, e.clientY, 12);
});
document.addEventListener("pointerdown", (e) => {
  if (e.target.closest && e.target.closest("button:not(:disabled)")) burstAt(e.clientX, e.clientY, 28);
});
applyFx();

/* ---------- trang trí nền (DOM, nằm sau canvas): mây, hoa, bụi lấp lánh, có parallax theo chuột ---------- */
const decorEls = [];
const CLOUD_SVG = '<svg viewBox="0 0 240 140"><g fill="#fff"><circle cx="70" cy="84" r="42"/><circle cx="118" cy="60" r="52"/><circle cx="176" cy="86" r="40"/><rect x="34" y="84" width="180" height="42" rx="21"/></g></svg>';
const daisySvg = () => '<svg viewBox="-50 -50 100 100"><g fill="#fff" stroke="rgba(150,170,190,.35)" stroke-width="2">' +
  Array.from({ length: 8 }, (_, i) => `<ellipse cx="0" cy="-27" rx="12" ry="21" transform="rotate(${i * 45})"/>`).join("") +
  '</g><circle r="15" fill="#FFA826"/><circle cx="-4" cy="-4" r="6" fill="#FFD36B"/></svg>';
const peachSvg = () => '<svg viewBox="-50 -50 100 100"><g fill="#FFB3A7" stroke="#F4907F" stroke-width="2.5">' +
  Array.from({ length: 5 }, (_, i) => `<circle cx="0" cy="-26" r="20" transform="rotate(${i * 72})"/>`).join("") +
  '</g><circle r="14" fill="#FFD54F" stroke="#F5B01C" stroke-width="2.5"/></svg>';
const STAR_SVG = '<svg viewBox="-30 -30 60 60"><path d="M0-28Q3-3 28 0Q3 3 0 28Q-3 3-28 0Q-3-3 0-28Z" fill="#fff" fill-opacity=".85"/></svg>';

function buildDecor() {
  const root = document.getElementById("decor"); if (!root) return;
  const add = (html, x, y, w, depth, phase) => {
    const d = document.createElement("div"); d.className = "dc"; d.style.left = x + "%"; d.style.top = y + "%"; d.style.width = w;
    d.dataset.d = depth;
    const f = document.createElement("div"); f.className = "float";
    f.style.animationDelay = `${-phase}s`; f.style.animationDuration = `${6 + ((phase * 1.7) % 4)}s`;
    f.innerHTML = html; d.append(f); root.append(d); decorEls.push(d);
  };
  // [x%, y%, rộng vw, độ sâu, pha]
  for (const [x, y, w, d, ph] of [[22.5, 37, 21, .25, 0], [33, 26, 11, .4, 1.2], [72, 23, 24, .3, .6], [66, 19, 10, .45, 2.0], [81.5, 60, 18, .35, 1.6], [21, 68, 14, .5, .9]])
    add(CLOUD_SVG, x, y, w + "vw", d, ph);
  // [loại, x%, y%, kích thước px]
  [["daisy", 25.6, 19, 34], ["daisy", 82.3, 34, 40], ["peach", 78.3, 35.3, 34], ["daisy", 14.8, 57.9, 36], ["peach", 18.6, 57.6, 30], ["daisy", 28.5, 75.7, 26]]
    .forEach(([k, x, y, sz], i) => add(k === "daisy" ? daisySvg() : peachSvg(), x, y, sz + "px", .7, i * 1.3));
  const dot = (col) => `<i style="display:block;padding-top:100%;border-radius:50%;background:${col}"></i>`;
  [[70.5, 12.2, 22, "#FFC9A8"], [17.4, 51, 18, "#FFC9A8"], [82.4, 43.5, 16, "#9ADFC3"], [16.6, 24.8, 14, "#fff"], [60.7, 12.3, 12, "#fff"],
   [28.3, 16.6, 8, "#fff"], [84.6, 31.4, 12, "#fff"], [84.6, 42, 14, "#fff"], [83.7, 67.6, 12, "#fff"], [11.3, 55.9, 12, "#fff"], [29, 70.7, 14, "#fff"]]
    .forEach(([x, y, sz, col], i) => add(dot(col), x, y, sz + "px", .85, i * .8));
  let sd = 7; const rnd = () => ((sd = (sd * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 24; i++) add(i % 3 ? dot("rgba(255,255,255,.75)") : STAR_SVG, 6 + rnd() * 88, 6 + rnd() * 86, (6 + rnd() * 12) + "px", .6 + rnd() * .4, rnd() * 6);
  add(STAR_SVG, 95.5, 93, 46 + "px", .3, 1);
  updateDecor(true);
}
let decLastX = 9, decLastY = 9;
function updateDecor(force) {
  if (!force && Math.abs(ptr.sx - decLastX) < 0.002 && Math.abs(ptr.sy - decLastY) < 0.002) return;
  decLastX = ptr.sx; decLastY = ptr.sy;
  for (const d of decorEls) {
    const k = +d.dataset.d;
    d.style.transform = `translate(-50%,-50%) translate(${(-ptr.sx * k * 26).toFixed(1)}px,${(-ptr.sy * k * 16).toFixed(1)}px)`;
  }
}
buildDecor();

/* ---------- vòng lặp ---------- */
const clamp01 = (x) => Math.min(1, Math.max(0, x));
const outCubic = (p) => 1 - Math.pow(1 - p, 3);
const outBack = (p) => 1 + 2.70158 * Math.pow(p - 1, 3) + 1.70158 * Math.pow(p - 1, 2);
let last = performance.now();
function tick(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (level) {
    for (const t of tileAt.values()) {                                              // cầu trồi lên / thụt xuống
      const u = t.userData; if (!u.bridge) continue;
      u.o += (u.openT - u.o) * Math.min(1, dt * 9); if (Math.abs(u.openT - u.o) < .003) u.o = u.openT;
      t.scale.set(1, .06 + .94 * u.o, 1);                                         // cầu đóng = bóng mờ mỏng, mở = ô đầy đủ
      t.material.transparent = t.children[0].material.transparent = true;
      t.material.opacity = t.children[0].material.opacity = .3 + .7 * u.o; u.sh.visible = u.o > .5;
    }
    if (hop) {
      hop.t += dt / rollDur; const p = clamp01(hop.t), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
      hop.g.position.set(hop.x0 + hop.dx * e, .48 + Math.sin(Math.PI * p) * .32, hop.z0 + hop.dz * e);
      if (p >= 1) finishHop();
    }
    if (cubePop < 1) { cubePop = Math.min(1, cubePop + dt / .35); cubes.forEach((g) => g.scale.setScalar(Math.max(.001, outBack(cubePop)))); }
    if (status === "fell" && cubeFall) {
      fallT += dt; const f = cubeFall;
      f.g.position.set(f.x0 + f.dx * .7 * fallT, .48 - 12 * fallT * fallT, f.z0 + f.dz * .7 * fallT);
      f.g.rotation.set(f.dz * fallT * 2.5, 0, -f.dx * fallT * 2.5);
      if (fallT > .9) loadLevel(idx);
    }
    if (status === "intro") {
      introT += dt;
      for (const m of tiles) m.position.y = (1 - outCubic(clamp01((introT - m.userData.delay) / 0.5))) * 5;
      blk.scale.setScalar(Math.max(0.001, outBack(clamp01((introT - 0.5) / 0.5))));
      if (introT > 1.05) { status = "idle"; blk.scale.setScalar(1); hud(); }
    }
    if (anim) {
      anim.t += dt / anim.dur;
      const p = clamp01(anim.t), e = p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
      anim.pivot.rotation[anim.axis] = anim.ang * e;
      if (p >= 1) finishRoll();
    }
    if (status === "fell" && fall) {
      fallT += dt;
      const a = Math.min(fall.maxAng, 0.5 * fall.alpha * fallT * fallT);          // đổ nhanh dần
      fall.pivot.rotation[fall.axis] = fall.base + fall.sign * a;
      fall.pivot.position.set(fall.x0 + fall.dc * 0.7 * fallT, -12 * fallT * fallT, fall.z0 + fall.dr * 0.7 * fallT);
      if (fallT > 0.9) loadLevel(idx);
    }
    if (status !== "intro") {                                                      // tile lún nhẹ dưới khối (lò xo)
      for (const [key, t] of tileAt) {
        const u = t.userData, target = -(pressed.get(key) || 0);
        if (u.broken) { t.position.y = -14 * Math.max(0, fallT - 0.05) ** 2; continue; }   // ô giòn vỡ rơi theo khối
        u.vy += (-190 * (u.dy - target) - 15 * u.vy) * dt; u.dy += u.vy * dt; t.position.y = u.dy;
      }
    }
    if (splitMode && status === "idle") {                                          // khối đang điều khiển nhấp nhô + vòng xoay
      cubes.forEach((g, i) => { const on = i === es.split.active;
        g.position.y = .48 + (on ? Math.sin(now / 260) * .04 : 0); g.userData.ring.rotation.y = now / 700; });
    }
    if (status === "idle" && !splitMode) {                                         // squishy: nở chậm + thở nhẹ
      sq.v += (-36 * sq.a - 9.6 * sq.v) * dt; sq.a += sq.v * dt;
      applySquish(sq.a + Math.sin(now / 650) * 0.01);
    }
    if (status === "won") {
      winT += dt; const e = clamp01(winT / 0.55);
      blk.position.y = winY - 2.4 * e * e;
      if (e >= 1) blk.visible = false;
      if (winT > 1.6 && !resultShown) showResult();   // chờ người chơi chọn bước tiếp theo
    }
    if (level.goal) {
      heart.position.set(level.goal[1], 0.95 + Math.sin(now / 450) * 0.07, level.goal[0]);
      heart.rotation.y = az;
    }
    if (inMenu) { az += dt * 0.12; azT = az; }          // menu: camera tự xoay chậm
    else if (!dragging) az += (azT - az) * Math.min(1, dt * 10);
    const par = R * 0.045, rx = Math.cos(az), rz = -Math.sin(az);   // camera lệch nhẹ theo chuột
    cam.position.set(center.x + R * Math.cos(el) * Math.sin(az) + rx * ptr.sx * par,
      center.y + R * Math.sin(el) - ptr.sy * par * 0.6,
      center.z + R * Math.cos(el) * Math.cos(az) + rz * ptr.sx * par);
    cam.lookAt(center);
    fxUpdate(dt);
  }
  renderer.render(scene, cam);
  requestAnimationFrame(tick);
}

fetch("/api/levels").then((r) => r.json()).then((data) => {
  levels = data; loadLevel(0); requestAnimationFrame(tick); refreshMenu();
}).catch(() => { $("msg").textContent = "Chưa tải được màn chơi — hãy chạy bằng: python serve.py"; });
