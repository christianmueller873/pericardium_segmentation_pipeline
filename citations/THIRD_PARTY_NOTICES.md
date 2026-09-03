# Third party data, software, and citation notices

This repository separates the project software license from the terms that
apply to datasets, source images, third party tools, and model weights. It does
not redistribute CT volumes, DICOM files, training labels, or patient linked
manifests.

The [MIT license](LICENSE) applies to the project software and documentation
and preserves the University Medicine Essen notice for retained SAROS code. It
does not relicense any dataset, source image collection, third party software,
or model checkpoint.

## SAROS and TCIA

Agent 1 was developed from the SAROS body region workflow. Local provenance
records use the September 2023 SAROS information spreadsheet and therefore
identify the training source as SAROS Version 1.

- SAROS source code: University Medicine Essen, MIT License,
  <https://github.com/UMEssen/saros-dataset>.
- SAROS data page: <https://www.cancerimagingarchive.net/analysis-result/saros/>.
- SAROS Version 1 segmentations and information spreadsheet: CC BY 4.0.
- SAROS CT images: obtained from 28 TCIA collections. The originating
  collection retains its own access and license terms, which include CC BY
  3.0, CC BY-NC 3.0, CC BY 4.0, and controlled access terms.
- TCIA policy: <https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/>.

Required SAROS data citation:

Koitka, S., Baldini, G., Kroll, L., van Landeghem, N., Haubold, J., Sung Kim,
M., Kleesiek, J., Nensa, F., & Hosch, R. (2023). *SAROS – A large,
heterogeneous, and sparsely annotated segmentation dataset on CT imaging data
(SAROS) (Version 1).* The Cancer Imaging Archive.
<https://doi.org/10.25737/SZ96-ZG60>

Recommended SAROS publication:

Koitka, S., Baldini, G., Kroll, L., van Landeghem, N., Pollok, O. B., Haubold,
J., Pelka, O., Kim, M., Kleesiek, J., Nensa, F., & Hosch, R. (2024). *SAROS: A
dataset for whole-body region and organ segmentation in CT imaging.* Scientific
Data, 11. <https://doi.org/10.1038/s41597-024-03337-6>

TCIA citation:

Clark, K., Vendt, B., Smith, K., Freymann, J., Kirby, J., Koppel, P., Moore,
S., Phillips, S., Maffitt, D., Pringle, M., Tarbox, L., & Prior, F. (2013).
*The Cancer Imaging Archive: Maintaining and Operating a Public Information
Repository.* Journal of Digital Imaging, 26(6), 1045–1057.
<https://doi.org/10.1007/s10278-013-9622-7>

## TotalSegmentator

Agent 2 pretraining used 947 CT volumes selected from Version 2.0.1 of the
1,228 case TotalSegmentator dataset. The training manifests contain 805 cases
for training and 142 for validation. Pseudolabels were generated from the
`pericardium` output of the `trunk_cavities` task, followed by removal of 10%
of the positive axial support at each end.

- TotalSegmentator CT dataset Version 2.0.1: CC BY 4.0,
  <https://doi.org/10.5281/zenodo.10047292>.
- TotalSegmentator software and the `trunk_cavities` task: Apache License 2.0.
  The audited baseline is documented in the
  [Version 2.18.0 README](https://github.com/wasserth/TotalSegmentator/blob/v2.18.0/README.md)
  and [license](https://github.com/wasserth/TotalSegmentator/blob/v2.18.0/LICENSE).
- The generation log records the task and trimming rule but not the installed
  TotalSegmentator package version. Version 2.18.0 was present when this
  repository was audited on 2026-09-03; it is a reproduction baseline, not a
  claim about the unrecorded historical run version.

TotalSegmentator dataset citation:

Wasserthal, J. (2023). *Dataset with segmentations of 117 important anatomical
structures in 1228 CT images* (Version 2.0.1). Zenodo.
<https://doi.org/10.5281/zenodo.10047292>

TotalSegmentator software citation:

Wasserthal, J., Breit, H.-C., Meyer, M. T., Pradella, M., Hinck, D., Sauter,
A. W., Heye, T., Boll, D., Cyriac, J., Yang, S., Bach, M., & Segeroth, M.
(2023). *TotalSegmentator: Robust Segmentation of 104 Anatomic Structures in CT
Images.* Radiology: Artificial Intelligence, 5.
<https://doi.org/10.1148/ryai.230024>

TotalSegmentator also requests citation of nnU Net:

Isensee, F., Jaeger, P. F., Kohl, S. A. A., Petersen, J., & Maier-Hein, K. H.
(2021). *nnU-Net: a self-configuring method for deep learning based biomedical
image segmentation.* Nature Methods, 18, 203–211.
<https://doi.org/10.1038/s41592-020-01008-z>

## Demo source record

The recording shows a 512 × 512 × 136 CT described during project preparation
as public SAROS and TCIA data. The recording and repository do not reveal the
SAROS case number or originating TCIA collection, and local inspection could
not identify it reliably. Before making the repository public, record the
exact case and source collection here, then apply that collection's citation,
license, and access terms. The CT volume itself is not included in this
repository.

## Model weight distribution

The GitHub Release checkpoints are separate artifacts from the MIT licensed
software. Agent 1 learned from SAROS and TCIA material. Agent 2 learned from
TotalSegmentator CTs and derived pseudolabels, then from 19 locally controlled
gold standard cases that are not redistributed.

Before publishing the checkpoint assets, document authorization to distribute
each trained weight file, choose explicit model weight terms, and include this
notice and the corresponding model card in each archive. Until those items are
complete, the checkpoint release should remain draft or private.
