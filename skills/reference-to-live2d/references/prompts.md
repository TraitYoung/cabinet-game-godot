# 可复用生成模板

以下是推荐模板，不是历史 T-pose 的原始提示词。替换方括号内容并附上对应参考图，实际运行后保存完整提示词。修改本地图像前先查看原图；按当前 image-generation skill 使用工具，透明输出要保留真实 alpha。

## T-pose 与三视图

```text
Use case: identity-preserve.
Asset type: character reference source, one view per image.
The reference is the approved character identity and outfit.
Draw the same [adult character] in a clean [front/back/side] T-pose view.
Preserve face, hairstyle, head-to-body proportions, outfit layers, colors,
accessories and illustration style. Include the full head, hands and shoe soles.
Front/back: arms horizontal, unobstructed silhouette, no foreshortening.
Side: consistent profile and garment depth.
Use [canvas/framing] and a plain background for measurement.
No labels, grids, captions or extra characters.
```

逐张对照主参考，不假定独立生成的视图天然同尺度。

## 完整头部候选

```text
Use case: identity-preserve.
Asset type: coherent head master for Live2D layer extraction.
The supplied T-pose is the authoritative identity reference.
Draw the complete head, hair, face, ears, accessories and short neck together.
Preserve [specific face, eye shape, expression, hair and lighting details].
Use [measured ratios] as relationships, not separately pasted features.
Keep continuous skin/hair shading and the whole hair silhouette.
Use [background/canvas]. No redesign, enlarged eyes, isolated features or atlas.
```

原图脸部已认可时可以直接原位分层；未通过审阅的头部只作为候选保存。

## 隐藏底层与前景遮罩

```text
Use case: precise-object-edit.
Asset type: registered hidden skin underpainting.
Keep exactly the original canvas, scale and position.
Only in [head region], replace hair and facial markings with a featureless
skin-tone base matching the original contour and shading. It will sit behind
the original visible pixels, not replace them. Keep the rest unchanged.
```

```text
Use case: precise-object-edit.
Asset type: foreground segmentation matte.
Keep exactly the original canvas, scale and coordinates.
Render the original character silhouette solid white and all background/gaps
solid black, with antialiased edges. Include fine hair, glasses frames, fingers
and shoes; retain gaps between strands, fingers and legs.
No internal texture, shading, labels or new character drawing.
```

检查镜片后方头发，不把镜片区域全部清空。

### 已有头部的眼眉后方补画

已有母图需要修复眨眼接缝时，保留完整头部，不要求移除全部头发。只从生成结果取所需隐藏区域，后续以原图差异分层保留可见五官。

```text
Use case: precise-object-edit.
Asset type: registered hidden skin plate for an existing Live2D head.
Edit the supplied [width × height] head crop. Keep framing, scale, head
position, hair, accessories, nose, mouth, cheeks, chin and neck unchanged.
Only remove both eyes, including pupils, eye whites, lashes and lid marks,
and both eyebrows. Replace their regions with continuous featureless skin
matching the surrounding shading. Preserve all hair strands crossing them.
No eye sockets, new eyelid lines, redesign or new expression.
Opaque interior skin and genuine transparency outside the character.
```

核对真实构图、尺寸及内部 alpha；生成器声明保持位置不代表完成注册。颈部需要补画时另写局部要求，明确保留原画可见衣领与肩线。

## 自然站姿母图

```text
Use case: identity-preserve.
Asset type: natural standing master for Live2D reconstruction.
Use the T-pose as the authoritative design and proportion reference.
Generate a coherent new standing body: redraw shoulders, armholes and folds
for hanging arms rather than rotating the original T-pose sleeves.
Preserve [identity, outfit, materials, accessories and illustration style].
Pose: relaxed upright front view, gently sloping shoulders, natural clavicles
and armholes, arms near the sides, relaxed elbows/hands, gravity-driven folds.
Preserve [leg stance/proportions]. Registration: [canvas], [center line],
[crown/chin/neck/skirt/sole heights]. Keep uniform whole-body scale.
Genuinely transparent alpha, clean edges, no background or floor shadow.
No squared raised shoulders, pasted sleeve ends, isolated parts, anatomical
distortion, added props, text or layout changes. Do not crop feet or hair.
```

保留原图脸部时仍可先生成完整站姿检查整体协调；组装时去掉生成头部，沿用原头部与颈部像素，并检查衔接。
