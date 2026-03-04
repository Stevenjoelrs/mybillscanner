package com.example.billscanner;

import com.google.mlkit.vision.text.Text;
import java.util.*;
import java.util.regex.*;

public class BillAnalyzer {
    private static final Map<String, long[][]> RANGES = new HashMap<>();
    static {
        RANGES.put("10", new long[][]{{67250001L, 67700000L}, {76310012L, 85139995L}});
        RANGES.put("20", new long[][]{{87280145L, 91646549L}, {118700001L, 119600000L}});
        RANGES.put("50", new long[][]{{77100001L, 77550000L}, {108050001L, 108500000L}});
    }

    public static class DetectedSerial {
        public final String fullText;
        public final String serialDigits;
        public final boolean isObserved;

        public DetectedSerial(String fullText, String serialDigits, boolean isObserved) {
            this.fullText = fullText;
            this.serialDigits = serialDigits;
            this.isObserved = isObserved;
        }
    }

    public static class AnalysisResult {
        public final String status;
        public final List<DetectedSerial> detectedSerials;

        public AnalysisResult(String status, List<DetectedSerial> detectedSerials) {
            this.status = status;
            this.detectedSerials = detectedSerials;
        }
    }

    public AnalysisResult analyze(Text visionText, boolean showDebug) {
        String detectedDenom = null;
        List<String> allSerialsFound = new ArrayList<>();
        List<DetectedSerial> historyEntries = new ArrayList<>();
        boolean seriesBFound = false;
        StringBuilder debugLog = new StringBuilder("DEBUG: ");

        for (Text.TextBlock block : visionText.getTextBlocks()) {
            for (Text.Line line : block.getLines()) {
                String rawText = line.getText().toUpperCase().trim();
                if (rawText.contains("DIEZ") || rawText.contains("10")) detectedDenom = "10";
                else if (rawText.contains("VEINTE") || rawText.contains("20")) detectedDenom = "20";
                else if (rawText.contains("50") || rawText.contains("CINCUENTA")) detectedDenom = "50";
                
                if (rawText.matches(".*\\bB\\b.*") || rawText.contains("SERIE B")) {
                    seriesBFound = true;
                }
            }
        }

        for (Text.TextBlock block : visionText.getTextBlocks()) {
            for (Text.Line line : block.getLines()) {
                String rawText = line.getText().toUpperCase().trim();
                if (showDebug) debugLog.append("[").append(rawText).append("] ");

                String cleanText = rawText.replace("O", "0").replace("I", "1").replace("L", "1");
                
                Matcher mFull = Pattern.compile("(\\d{9})\\s*([A-Z])").matcher(cleanText);
                while (mFull.find()) {
                    String serial = mFull.group(1);
                    String letter = mFull.group(2);
                    
                    if (detectedDenom != null) {
                        boolean isObserved = checkIfObserved(serial, detectedDenom);
                        String entry = detectedDenom + " BS - " + serial + " " + letter;
                        historyEntries.add(new DetectedSerial(entry, serial, isObserved));
                    }
                }

                Matcher m = Pattern.compile("\\d{8,9}").matcher(cleanText);
                while (m.find()) {
                    allSerialsFound.add(m.group());
                }
            }
        }

        StringBuilder result = new StringBuilder();
        if (detectedDenom != null) {
            result.append("VALOR: ").append(detectedDenom).append(" Bs\n");
        } else {
            result.append("Buscando Denominación...\n");
        }
        result.append("SERIE B: ").append(seriesBFound ? "SI" : "NO").append("\n");
        if (showDebug) result.append("SERIALES: ").append(allSerialsFound.toString()).append("\n");

        String status;
        if (detectedDenom != null && seriesBFound && !allSerialsFound.isEmpty()) {
            boolean observed = false;
            String foundS = "";
            for (String s : allSerialsFound) {
                if (checkIfObserved(s, detectedDenom)) {
                    observed = true;
                    foundS = s;
                    break;
                }
            }
            if (observed) {
                status = "⚠️ ALERTA: " + foundS + " OBSERVADO\n" + result.toString();
            } else {
                status = "✅ VALIDO\n" + result.toString();
            }
        } else {
            status = result.toString();
        }
        
        if (showDebug) {
            status += "\n" + (debugLog.length() > 100 ? debugLog.substring(0, 100) + "..." : debugLog.toString());
        }

        return new AnalysisResult(status, historyEntries);
    }

    private boolean checkIfObserved(String serial, String denom) {
        long[][] denomRanges = RANGES.get(denom);
        if (denomRanges == null) return false;
        try {
            long val = Long.parseLong(serial);
            for (long[] r : denomRanges) {
                if (val >= r[0] && val <= r[1]) return true;
            }
        } catch (Exception e) {}
        return false;
    }

    // Deprecated but kept for compatibility if needed
    public String processText(Text visionText) {
        return analyze(visionText, false).status;
    }
}
