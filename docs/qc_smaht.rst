========================
Quality metrics in SMaHT
========================

The handling of Quality Metrics in the SMaHT portal is different from the one in 4DN and CGAP (CGAP supports this way as well). It is more generic in general and uses only a single quality metrics item type in the portal, i.e., ``QualityMetricGeneric``. The new approach removes much of the complexity in Tibanna that was required to handle the different QC types and moves this complexity to the pipeline side.