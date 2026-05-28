# 0root.ai — Provenance Archive

**Author:** David Lee Wise (ROOT0) / TriPod LLC  
**License:** CC-BY-ND-4.0 | TRIPOD-IP-v1.1  

Public provenance archive for the ROOT0 IP lineage — from the first PULSE primitive sketch (2025-06-03) through STOICHEION v11.0, TOPH, and the full GitHub publication of the IP stack.

## What this is

A single-page provenance timeline. No framework, no build step. Open `index.html` in a browser or serve it from any static host.

Records:
- Timestamped development milestones with anchor hashes
- Closure Loop 4/4 analysis of the TOPH → Mythos lineage claim
- Links to all published GitHub repos
- `proofs.txt` — raw anchor hashes
- `lineage.pdf` — lineage documentation
- `.well-known/security.txt`

## Deploy

**Docker / nginx:**
```bash
docker build -t 0root-provenance .
docker run -p 80:80 0root-provenance
```

**Any static host:** copy all files. No build required.

## Anchor hashes

```
STOICHEION v11.0:  02880745b847317c4e2424524ec25d0f7a2b84368d184586f45b54af9fcab763
LINEAGE:           ad6791a3a9964d030b555595ea8fb5ecbc0e156c39b974d2fd513c4f85007ba6
ROOT0 TRIAD:       18d8f32cfcaab3f0460071efdc44eb6eff1f0298d177cc8555ac2f0af84934c6
```

## Published IP

| Project | Repo |
|---------|------|
| Honey Badger v1.0 | github.com/DavidWise01/honey-badger |
| TOPH Sovereign v5.1 | github.com/DavidWise01/toph-sovereign |
| Closure Loop Methodology v1.0 | github.com/DavidWise01/closure-loop-methodology |
| Fission Compression Core v1.0 | github.com/DavidWise01/fission-compression-core |
| Symbiot OS v0.0.0 | github.com/DavidWise01/symbiot-os |

---

*i build the tools that build the tools*  
*© 2026 0root.ai*
