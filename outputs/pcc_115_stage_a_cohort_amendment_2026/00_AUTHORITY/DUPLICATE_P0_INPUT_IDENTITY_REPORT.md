# Duplicate P0 input identity report

本审计仅读取两个病例各自的current Timepoint_1 T1c与current mask；未读取future、target或后续timepoint。

## Hash canonicalization

- 原始文件SHA-256：NIfTI文件原始字节。
- 体素SHA-256：nibabel.get_fdata(dtype=float32)后C-contiguous数组字节。
- 归一化与模型输入SHA-256：仓库prepare_current_only_inputs输出数组的C-contiguous字节。

## Pairwise result

- raw_t1c_file_identical: true
- raw_mask_file_identical: true
- t1c_voxel_identical: true
- mask_voxel_identical: true
- t1c_affine_identical: true
- mask_affine_identical: true
- normalized_t1c_identical: true
- binary_mask_identical: true
- model_input_tensor_identical: true

结论：**A: 两病例的原始和预处理双通道输入完全相同**。
