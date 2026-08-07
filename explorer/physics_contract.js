/*
 * iQuant4 browser/Python physics contract.
 *
 * This dependency-free module mirrors the canonical Python defaults and the
 * closed-form calculations used by iqcore.fiber and iq4comm.qkd.  It is usable
 * both from the offline explorer (global `IQ4Physics`) and Node.js contract
 * tests (`require(...)`).  Change a constant or equation here only together
 * with the corresponding Python implementation and parity tests.
 */
(function (root, factory) {
  "use strict";
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.IQ4Physics = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const LN2 = Math.log(2);
  const LN10 = Math.log(10);
  const H_J_S = 6.62607015e-34;
  const C_M_PER_S = 2.99792458e8;

  const DEFAULTS = Object.freeze({
    attenuationDbPerKm: 0.2,
    dispersionPsNmKm: 17.0,
    gammaPerWPerKm: 1.3,
    referenceWavelengthNm: 1550.0,
    symbolRateBaud: 32e9,
    noiseFigureDb: 5.0,
    detectorEfficiency: 0.5,
    darkCountProbability: 1e-6,
    misalignment: 0.02,
    errorCorrectionEfficiency: 1.16,
    mu: 0.5,
    siftFactor: 0.5,
    ramanCoefficientPerKmPerNm: 4.708129334491568e-10,
    ramanFilterBandwidthNm: 0.01,
    ramanGateTimeS: 1e-10,
    quantumWavelengthNm: 1550.0,
    wssBandwidth3dbGhz: 40.0,
    wssOrder: 3,
    wssInsertionLossDb: 5.0,
    wssIntegrationPoints: 2001,
  });

  const FORMATS = Object.freeze({
    OOK: Object.freeze({ bitsPerSymbol: 1, order: 2, kind: "ook" }),
    QPSK: Object.freeze({ bitsPerSymbol: 2, order: 4, kind: "psk" }),
    "16QAM": Object.freeze({ bitsPerSymbol: 4, order: 16, kind: "qam" }),
    "64QAM": Object.freeze({ bitsPerSymbol: 6, order: 64, kind: "qam" }),
  });

  const FEC_CODES = Object.freeze({
    none: Object.freeze({ thresholdBer: 3.8e-3, rate: 1.0 }),
    "RS(255,239)": Object.freeze({
      thresholdBer: 6.536270487947853e-5,
      rate: 239 / 255,
    }),
    KP4: Object.freeze({
      thresholdBer: 1.9390312171212545e-4,
      rate: 514 / 544,
    }),
    "HD-FEC-7%": Object.freeze({ thresholdBer: 3.8e-3, rate: 93 / 100 }),
    "SD-FEC-20%": Object.freeze({ thresholdBer: 2.0e-2, rate: 100 / 120 }),
  });

  function log2(x) { return Math.log(x) / LN2; }
  function log10(x) { return Math.log(x) / LN10; }
  function asinh(x) { return Math.log(x + Math.sqrt(x * x + 1)); }

  function erfc(x) {
    // Abramowitz-Stegun 7.1.26; sufficient for interactive BER display.
    const z = Math.abs(x);
    const t = 1 / (1 + 0.3275911 * z);
    const y = t * (0.254829592 + t * (-0.284496736
      + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429))));
    const result = y * Math.exp(-z * z);
    return x >= 0 ? result : 2 - result;
  }

  function qFunction(x) { return 0.5 * erfc(x / Math.SQRT2); }

  function binaryEntropy(x) {
    if (x <= 0 || x >= 1) return 0;
    return -x * log2(x) - (1 - x) * log2(1 - x);
  }

  function fiberTransmissivity(distanceKm, attenuationDbPerKm) {
    const loss = attenuationDbPerKm ?? DEFAULTS.attenuationDbPerKm;
    if (distanceKm < 0) throw new RangeError("distanceKm must be non-negative");
    if (loss < 0) throw new RangeError("attenuationDbPerKm must be non-negative");
    return Math.pow(10, -loss * distanceKm / 10);
  }

  function effectiveLengthKm(distanceKm, attenuationDbPerKm) {
    const loss = attenuationDbPerKm ?? DEFAULTS.attenuationDbPerKm;
    const alpha = loss * LN10 / 10;
    if (alpha === 0) return distanceKm;
    return -Math.expm1(-alpha * distanceKm) / alpha;
  }

  function ramanPathIntegralKm(distanceKm, options) {
    const opts = options || {};
    const pumpLoss = opts.pumpAttenuationDbPerKm
      ?? DEFAULTS.attenuationDbPerKm;
    const quantumLoss = opts.quantumAttenuationDbPerKm
      ?? DEFAULTS.attenuationDbPerKm;
    const direction = opts.propagationDirection ?? "co";
    if (distanceKm < 0) throw new RangeError("distanceKm must be non-negative");
    if (pumpLoss < 0 || quantumLoss < 0) {
      throw new RangeError("attenuation must be non-negative");
    }
    if (direction !== "co" && direction !== "counter") {
      throw new RangeError("propagationDirection must be 'co' or 'counter'");
    }
    if (distanceKm === 0) return 0;
    const alphaP = pumpLoss * LN10 / 10;
    const alphaQ = quantumLoss * LN10 / 10;
    if (direction === "counter") {
      const sum = alphaP + alphaQ;
      return sum === 0 ? distanceKm : -Math.expm1(-sum * distanceKm) / sum;
    }
    const delta = alphaP - alphaQ;
    if (delta === 0) return distanceKm * Math.exp(-alphaQ * distanceKm);
    if (Math.abs(delta * distanceKm) < 1e-6) {
      return Math.exp(-alphaQ * distanceKm)
        * (-Math.expm1(-delta * distanceKm) / delta);
    }
    return (Math.exp(-alphaQ * distanceKm) - Math.exp(-alphaP * distanceKm))
      / delta;
  }

  function ramanBackgroundYield(options) {
    const opts = options || {};
    const wavelengthNm = opts.quantumWavelengthNm
      ?? DEFAULTS.quantumWavelengthNm;
    const path = ramanPathIntegralKm(opts.distanceKm, opts);
    const receivedW = opts.classicalTotalPowerW
      * (opts.ramanCoefficientPerKmPerNm
        ?? DEFAULTS.ramanCoefficientPerKmPerNm)
      * (opts.filterBandwidthNm ?? DEFAULTS.ramanFilterBandwidthNm)
      * path;
    const photonEnergy = H_J_S * C_M_PER_S / (wavelengthNm * 1e-9);
    return receivedW / photonEnergy
      * (opts.gateTimeS ?? DEFAULTS.ramanGateTimeS)
      * (opts.detectorEfficiency ?? DEFAULTS.detectorEfficiency);
  }

  function roadmFilterStages(nRoadms) {
    return nRoadms <= 0 ? 0 : nRoadms + 1;
  }

  function roadmInsertionLossDb(nRoadms, insertionLossDb) {
    if (nRoadms <= 0) return 0;
    const stageLoss = insertionLossDb ?? DEFAULTS.wssInsertionLossDb;
    const expressNodes = Math.max(0, nRoadms - 2);
    return (2 * expressNodes + 2) * stageLoss;
  }

  function wssNarrowingPenaltyDb(nFilters, signalBandwidthHz, options) {
    if (nFilters < 1) throw new RangeError("nFilters must be at least one");
    const opts = options || {};
    const bandwidthHz = (opts.bandwidth3dbGhz
      ?? DEFAULTS.wssBandwidth3dbGhz) * 1e9;
    const order = opts.order ?? DEFAULTS.wssOrder;
    const nPoints = opts.nPoints ?? DEFAULTS.wssIntegrationPoints;
    if (nPoints < 2) throw new RangeError("nPoints must be at least two");
    const half = signalBandwidthHz / 2;
    const step = signalBandwidthHz / (nPoints - 1);
    let sum = 0;
    for (let index = 0; index < nPoints; index += 1) {
      const frequency = -half + index * step;
      const normalized = 2 * Math.abs(frequency) / bandwidthHz;
      const transmission = Math.exp(-LN2 * Math.pow(normalized, 2 * order));
      const cascaded = Math.pow(transmission, nFilters);
      sum += (index === 0 || index === nPoints - 1) ? cascaded / 2 : cascaded;
    }
    const passedFraction = sum * step / signalBandwidthHz;
    return passedFraction <= 0 ? Infinity : -10 * log10(passedFraction);
  }

  function channelSnrDb(options) {
    const opts = options || {};
    const attenuation = opts.attenuationDbPerKm
      ?? DEFAULTS.attenuationDbPerKm;
    const wavelengthNm = opts.wavelengthNm ?? DEFAULTS.referenceWavelengthNm;
    const symbolRate = opts.symbolRateBaud ?? DEFAULTS.symbolRateBaud;
    const spacing = opts.channelSpacingHz;
    const channelCount = opts.channelCount;
    const distance = opts.distanceKm;
    const gamma = opts.gammaPerWPerKm ?? DEFAULTS.gammaPerWPerKm;
    const dispersion = opts.dispersionPsNmKm ?? DEFAULTS.dispersionPsNmKm;
    const nfLinear = Math.pow(10,
      (opts.noiseFigureDb ?? DEFAULTS.noiseFigureDb) / 10);
    const gain = Math.pow(10, attenuation * distance / 10);
    const nSp = gain > 1 ? nfLinear * gain / (2 * (gain - 1)) : nfLinear / 2;
    const photonEnergy = H_J_S * C_M_PER_S / (wavelengthNm * 1e-9);
    const ase = nSp * photonEnergy * (gain - 1) * symbolRate;
    const alpha = attenuation * LN10 / 10;
    const leff = effectiveLengthKm(distance, attenuation);
    const asymptoticLeff = alpha > 0 ? 1 / alpha : distance;
    const cNmPerPs = C_M_PER_S * 1e-3;
    const beta2 = Math.abs(-dispersion * wavelengthNm * wavelengthNm
      / (2 * Math.PI * cNmPerPs));
    const wdmBandwidthThz = channelCount * spacing / 1e12;
    const symbolRateThz = symbolRate / 1e12;
    const argument = (Math.PI * Math.PI / 2) * beta2 * asymptoticLeff
      * wdmBandwidthThz * wdmBandwidthThz;
    const eta = ((8 / 27) * gamma * gamma * leff * leff * asinh(argument))
      / (Math.PI * beta2 * asymptoticLeff
        * symbolRateThz * symbolRateThz);
    const launchW = 1e-3 * Math.pow(10, opts.launchDbmPerChannel / 10);
    const snr = launchW / (ase + eta * launchW * launchW * launchW);
    return 10 * log10(snr);
  }

  function berTheory(format, ebn0Db) {
    const spec = FORMATS[format];
    if (!spec) throw new RangeError(`unsupported format ${format}`);
    const ebn0 = Math.pow(10, ebn0Db / 10);
    if (spec.kind === "ook") return qFunction(Math.sqrt(ebn0));
    if (spec.kind === "psk") return qFunction(Math.sqrt(2 * ebn0));
    const coefficient = (4 / spec.bitsPerSymbol)
      * (1 - 1 / Math.sqrt(spec.order));
    return coefficient * qFunction(Math.sqrt(
      3 * spec.bitsPerSymbol / (spec.order - 1) * ebn0));
  }

  function bb84DecoyKeyRate(transmissivity, backgroundYield, options) {
    const opts = options || {};
    const detectorEfficiency = opts.detectorEfficiency
      ?? DEFAULTS.detectorEfficiency;
    const dark = opts.darkCountProbability ?? DEFAULTS.darkCountProbability;
    const misalignment = opts.misalignment ?? DEFAULTS.misalignment;
    const errorCorrection = opts.errorCorrectionEfficiency
      ?? DEFAULTS.errorCorrectionEfficiency;
    const mu = opts.mu ?? DEFAULTS.mu;
    const sift = opts.siftFactor ?? DEFAULTS.siftFactor;
    const etaSystem = transmissivity * detectorEfficiency;
    const y0 = Math.min(2 * dark + backgroundYield, 1);
    const qMu = y0 + 1 - Math.exp(-etaSystem * mu);
    if (qMu <= 0) return 0;
    const eMu = (0.5 * y0 + misalignment
      * (1 - Math.exp(-etaSystem * mu))) / qMu;
    const y1 = y0 + etaSystem - y0 * etaSystem;
    const q1 = mu * Math.exp(-mu) * y1;
    const e1 = y1 > 0 ? (0.5 * y0 + misalignment * etaSystem) / y1 : 0.5;
    return Math.max(sift * (q1 * (1 - binaryEntropy(e1))
      - qMu * errorCorrection * binaryEntropy(eMu)), 0);
  }

  function tfScalingProxyKeyRate(transmissivity, backgroundYield, options) {
    const opts = options || {};
    const detectorEfficiency = opts.detectorEfficiency
      ?? DEFAULTS.detectorEfficiency;
    const dark = opts.darkCountProbability ?? DEFAULTS.darkCountProbability;
    const misalignment = opts.misalignment ?? DEFAULTS.misalignment;
    const errorCorrection = opts.errorCorrectionEfficiency
      ?? DEFAULTS.errorCorrectionEfficiency;
    const protocolEfficiency = opts.protocolEfficiency ?? 0.25;
    const interferometricError = opts.interferometricError ?? 0.02;
    const gainSignal = protocolEfficiency * detectorEfficiency
      * Math.sqrt(transmissivity);
    const y0 = 2 * dark + backgroundYield;
    const gain = y0 + gainSignal;
    const error = gain > 0
      ? (0.5 * y0 + (misalignment + interferometricError) * gainSignal) / gain
      : 0.5;
    return Math.max(DEFAULTS.siftFactor * gain
      * (1 - (1 + errorCorrection) * binaryEntropy(error)), 0);
  }

  function systemKeyRate(options) {
    const opts = options || {};
    const attenuation = opts.attenuationDbPerKm
      ?? DEFAULTS.attenuationDbPerKm;
    const perChannelW = 1e-3 * Math.pow(10, opts.launchDbmPerChannel / 10);
    const background = ramanBackgroundYield({
      classicalTotalPowerW: perChannelW * opts.channelCount,
      distanceKm: opts.distanceKm,
      pumpAttenuationDbPerKm: opts.pumpAttenuationDbPerKm ?? attenuation,
      quantumAttenuationDbPerKm: attenuation,
      propagationDirection: opts.propagationDirection ?? "co",
      ramanCoefficientPerKmPerNm: opts.ramanCoefficientPerKmPerNm,
      filterBandwidthNm: opts.filterBandwidthNm,
      gateTimeS: opts.gateTimeS,
      quantumWavelengthNm: opts.quantumWavelengthNm,
      detectorEfficiency: opts.detectorEfficiency,
    });
    const roadmLoss = roadmInsertionLossDb(
      opts.nRoadms ?? 0,
      opts.wssInsertionLossDb,
    );
    const transmissivity = fiberTransmissivity(opts.distanceKm, attenuation)
      * Math.pow(10, -roadmLoss / 10);
    if (opts.protocol === "tf") {
      return tfScalingProxyKeyRate(transmissivity, background, opts);
    }
    if (opts.protocol !== "dv") {
      throw new RangeError("browser contract supports 'dv' and exploratory 'tf'");
    }
    return bb84DecoyKeyRate(transmissivity, background, opts);
  }

  function systemOperatingPoint(options) {
    const opts = options || {};
    const format = FORMATS[opts.format];
    const fec = FEC_CODES[opts.fec];
    if (!format) throw new RangeError(`unsupported format ${opts.format}`);
    if (!fec) throw new RangeError(`unsupported FEC ${opts.fec}`);
    const symbolRate = opts.symbolRateBaud ?? DEFAULTS.symbolRateBaud;
    const occupied = symbolRate * (1 + opts.rolloff);
    const nRoadms = opts.nRoadms ?? 0;
    const narrowing = nRoadms > 0
      ? wssNarrowingPenaltyDb(roadmFilterStages(nRoadms), occupied, opts)
      : 0;
    // Match Python system_operating_point: apply narrowing as an equivalent
    // launch-power penalty before evaluating the GN model.
    const snrDb = channelSnrDb({
      ...opts,
      launchDbmPerChannel: opts.launchDbmPerChannel - narrowing,
      symbolRateBaud: symbolRate,
      channelSpacingHz: occupied,
    });
    const ebn0Db = snrDb - 10 * log10(format.bitsPerSymbol);
    const ber = berTheory(opts.format, ebn0Db);
    const closes = ber <= fec.thresholdBer;
    const capacityBps = closes
      ? opts.channelCount * symbolRate * format.bitsPerSymbol * fec.rate
      : 0;
    const keyRate = systemKeyRate(opts);
    const recommendationEligible = opts.protocol === "dv";
    return {
      ber,
      closes,
      capacityBps,
      keyRate,
      narrowingPenaltyDb: narrowing,
      roadmLossDb: roadmInsertionLossDb(nRoadms, opts.wssInsertionLossDb),
      modelStatus: recommendationEligible ? "research_model" : "scaling_proxy",
      recommendationEligible,
    };
  }

  return Object.freeze({
    DEFAULTS,
    FORMATS,
    FEC_CODES,
    fiberTransmissivity,
    effectiveLengthKm,
    ramanPathIntegralKm,
    ramanBackgroundYield,
    roadmFilterStages,
    roadmInsertionLossDb,
    wssNarrowingPenaltyDb,
    channelSnrDb,
    berTheory,
    bb84DecoyKeyRate,
    tfScalingProxyKeyRate,
    systemKeyRate,
    systemOperatingPoint,
  });
});
