#!/bin/bash

echo "Reconstructing FES from HILLS file..."

# Parameters
HILLS_FILE="results/HILLS"
OUTPUT_FILE="results/fes_final_analysis.txt"
CV_MIN="-3.0"
CV_MAX="3.0"
N_POINTS=300

# Use awk to reconstruct FES
# For each CV point, sum over all Gaussians: exp(-((cv-center)/sigma)^2/2) * height

cat > fes_calc.awk << 'AWKSCRIPT'
BEGIN {
  cv_min = -3.0
  cv_max = 3.0
  n_points = 300
  
  # Read HILLS file and store all Gaussians
  while ((getline line < "results/HILLS") > 0) {
    if (line ~ /^#/ || line ~ /^$/) continue
    
    n_fields = split(line, fields)
    if (n_fields < 5) continue
    
    cv = fields[2] + 0
    sigma = fields[3] + 0
    height = fields[4] + 0
    
    hills[n_hills] = cv
    sigmas[n_hills] = sigma
    heights[n_hills] = height
    n_hills++
  }
  close("results/HILLS")
  
  print "# FES Reconstruction from " n_hills " Gaussians"
  print "# CV (Å)  FES (kJ/mol)"
  
  # Reconstruct FES at each grid point
  for (i = 0; i < n_points; i++) {
    cv_grid = cv_min + (cv_max - cv_min) * i / (n_points - 1)
    fes = 0
    
    for (j = 0; j < n_hills; j++) {
      dx = (cv_grid - hills[j]) / sigmas[j]
      fes += heights[j] * exp(-dx * dx / 2)
    }
    
    printf "%.6f  %.6f\n", cv_grid, fes
  }
}
AWKSCRIPT

awk -f fes_calc.awk > "$OUTPUT_FILE"

echo "✅ FES reconstruction saved to $OUTPUT_FILE"
echo ""
echo "Statistics:"
grep -v "^#" "$OUTPUT_FILE" | awk '{print $2}' | awk '{if(NR==1||$1<min)min=$1; if(NR==1||$1>max)max=$1; sum+=$1} END {printf "  FES range: [%.1f, %.1f] kJ/mol\n  Mean FES: %.1f kJ/mol\n", min, max, sum/NR}'

# Extract barrier height
echo ""
echo "Barrier Analysis:"
echo "  Reactant basin (CV=-1.5Å):"
grep "^-1.5" "$OUTPUT_FILE" || awk 'NR>1 && $1>=-1.55 && $1<=-1.45' "$OUTPUT_FILE" | tail -1 | awk '{printf "    FES = %.1f kJ/mol\n", $2}'

echo "  Transition state (CV=0.0Å):"
awk 'NR>1 && $1>=-0.05 && $1<=0.05' "$OUTPUT_FILE" | tail -1 | awk '{printf "    FES = %.1f kJ/mol\n", $2}'

echo "  Product basin (CV=+1.5Å):"
awk 'NR>1 && $1>=1.45 && $1<=1.55' "$OUTPUT_FILE" | tail -1 | awk '{printf "    FES = %.1f kJ/mol\n", $2}'

rm -f fes_calc.awk
