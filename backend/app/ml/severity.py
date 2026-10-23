def severity(text, related=0):
    text=text.lower()
    factors={
      "reported_damage":30 if any(w in text for w in ["large","deep","severe","collapsed","broken"]) else 10,
      "safety_risk":25 if any(w in text for w in ["accident","danger","swerv","injur","exposed wire","unsafe"]) else 0,
      "sensitive_location":15 if any(w in text for w in ["school","hospital","children"]) else 0,
      "related_reports":min(15,related*5),
      "traffic_usage":10 if any(w in text for w in ["vehicles","traffic","busy"]) else 0,
      "historical_incidents":0}
    score=sum(factors.values())
    level="Low" if score<=25 else "Moderate" if score<=50 else "High" if score<=75 else "Critical"
    return {"score":score,"level":level,"factors":factors,
      "method":"Explainable text-based prototype. Visual damage and historical incidents are not inferred from images."}
