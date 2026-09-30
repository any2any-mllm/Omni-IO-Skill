import * as THREE from 'three'; import {GLTFLoader} from './vendor/GLTFLoader.js'; import {OrbitControls} from './vendor/OrbitControls.js';
const canvas=document.querySelector('#c'),stage=document.querySelector('#stage');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true,preserveDrawingBuffer:true}); renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.05;
const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(32,1,.001,20); camera.position.set(.30,.20,.34);
const controls=new OrbitControls(camera,canvas); controls.enableDamping=true; controls.dampingFactor=.06; controls.minDistance=.18; controls.maxDistance=.9; controls.target.set(0,0,0);
scene.add(new THREE.HemisphereLight(0xfff3da,0x544736,2.1)); const key=new THREE.DirectionalLight(0xffd58d,3);key.position.set(-2,3,4);scene.add(key);const rim=new THREE.DirectionalLight(0xc8d7ff,2);rim.position.set(3,1,-2);scene.add(rim);
const root=new THREE.Group(); scene.add(root); let model;
const markerData=[{el:document.querySelector('#h1'),p:new THREE.Vector3(.018,-.018,.036)},{el:document.querySelector('#h2'),p:new THREE.Vector3(-.012,.052,.035)}];
new GLTFLoader().load('./food_scan.glb',g=>{model=g.scene; model.rotation.z=-Math.PI/2; const box=new THREE.Box3().setFromObject(model),center=box.getCenter(new THREE.Vector3());model.position.sub(center);root.add(model);document.querySelector('#loading').style.opacity=0;setTimeout(()=>document.querySelector('#loading').remove(),450);window.exhibitReady=true;},undefined,e=>document.querySelector('#loading').textContent='Could not load model: '+e.message);
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()} new ResizeObserver(resize).observe(stage);
function labels(){if(!model)return; for(const m of markerData){const p=m.p.clone().applyMatrix4(model.matrixWorld).project(camera);m.el.style.left=`${(p.x*.5+.5)*stage.clientWidth}px`;m.el.style.top=`${(-p.y*.5+.5)*stage.clientHeight}px`;m.el.style.opacity=p.z<1?'1':'0'}}
function animate(){requestAnimationFrame(animate);controls.update();labels();renderer.render(scene,camera)}animate();
window.setView=(az,el)=>{const r=.43,a=THREE.MathUtils.degToRad(az),e=THREE.MathUtils.degToRad(el);camera.position.set(r*Math.cos(e)*Math.sin(a),r*Math.sin(e),r*Math.cos(e)*Math.cos(a));controls.target.set(0,0,0);controls.update()};
function reset(){window.setView(25,18)} canvas.addEventListener('dblclick',reset);reset();
