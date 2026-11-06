import type { CubismInternalModel } from "untitled-pixi-live2d-engine/cubism";

// The first Bina rig is made from flat parts and cannot support full SDK turns.
const PARAMETER_SCALE: Record<string, number> = {
  ParamAngleX: 0.18,
  ParamAngleY: 0.18,
  ParamAngleZ: 0.2,
  ParamBodyAngleX: 0.2,
  ParamBodyAngleY: 0.2,
  ParamBodyAngleZ: 0.2,
  ParamBodyLean: 0.2,
  ParamBreath: 0.35,
  ParamEyeBallX: 0.35,
  ParamEyeBallY: 0.35,
  ParamEyeBallForm: 0,
  ParamHairFront: 0.18,
  ParamHairBack: 0.25,
};

// Repaired heads use their authored turns and blinks without legacy face clamps.
const REPAIRED_BODY_SCALE: Record<string, number> = {
  ParamBodyAngleX: 0.1,
  ParamBodyAngleY: 0.1,
  ParamBodyAngleZ: 0.1,
  ParamBodyLean: 0.1,
  ParamBreath: 0.175,
};

export function stabilizeBinaRig(model: CubismInternalModel, registered = false) {
  const core = model.coreModel;
  const parameters = Array.from({ length: core.getParameterCount() }, (_, index) => ({
    index,
    id: core.getParameterId(index).getString().s,
  }));

  // Apply after focus, expressions and physics, without changing saved motion values.
  model.on("beforeModelUpdate", () => {
    for (const { index, id } of parameters) {
      const value = core.getParameterValueByIndex(index);
      const scale = (registered ? REPAIRED_BODY_SCALE : PARAMETER_SCALE)[id];
      if (scale !== undefined) core.setParameterValueByIndex(index, value * scale);
      // This rig collapses the entire mouth mesh at zero, including the lip outline.
      if (!registered && id === "ParamMouthOpenY") core.setParameterValueByIndex(index, Math.max(0.12, value));
    }
  });
}
