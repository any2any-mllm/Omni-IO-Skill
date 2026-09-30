# THD 0521-01 reconstruction package

The GLB is a watertight convex-envelope completion of the 620 observed points. This is a conservative engineering restoration: it preserves the measured coordinate frame, dimensions, boundary asymmetry, and thin-panel form while closing missing scan coverage without inventing detail.

## Interactive viewer

Because browsers restrict local model loading, serve this folder over HTTP:

```bash
python3 -m http.server 8000 --directory .
```

Then open `http://localhost:8000/viewer.html`.

The viewer includes toggles for measured points and mesh wireframe, plus two inspection hotspots.

## Files

- `thd_0521_01_reconstructed.glb` — completed model
- `thd_0521_01.ply` — original observed points
- `inspection_front.png`, `inspection_side.png`, `inspection_top.png` — orthographic inspection renders
- `turntable_360.mp4` — rotating inspection video
- `viewer.html` and `scan_data.json` — interactive viewer

Source units were not declared in the PLY, so dimensions remain in source units.
