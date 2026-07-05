def acl_risk_score(left_knee,right_knee,asymmetry,left_valgus,right_valgus,velocity,age,gender):
    score=0.0
    
    for knee in (left_knee,right_knee):
        score+=30 if knee>175 else 22 if knee>170 else 15 if knee>165 else 8 if knee>160 else 0
    for v in (left_valgus,right_valgus):
        score+=25 if v>25 else 18 if v>20 else 12 if v>15 else 6 if v>10 else 0
    score+=25 if asymmetry>30 else 18 if asymmetry>20 else 10 if asymmetry>10 else 0
    av=abs(velocity)
    score+=20 if av>500 else 15 if av>350 else 10 if av>200 else 0
    if (left_knee>170 or right_knee>170) and (left_valgus>20 or right_valgus>20): score+=20
    if asymmetry>20 and av>300: score+=10
    if age<25: score+=3
    if gender=='Female': score+=5
    return min(round(score),100)
