import streamlit as st
import pandas as pd
#import os

# Initialize session state for acknowledgment
if "acknowledged" not in st.session_state:
    st.session_state["acknowledged"] = False

# Acknowledgment logic
if not st.session_state["acknowledged"]:
    # Show the warning message
    st.warning("This app is meant only for guidance. All results should be independently verified. \n\nPlease click I acknowledge to continue using application")
    
    # Add an acknowledgment button
    if st.button("I Acknowledge"):
        st.session_state["acknowledged"] = True



#st.warning("This app is not meant for clinical use. All results should be independently verified.")

if st.session_state["acknowledged"]:
    # Define grading criteria and dose modification guidance for LUTATHERA and PLUVICTO
    grading_criteria = {
        'Lutathera': {
            'Thrombocytopenia': {
                'Grade 1': {'Platelet': {'min': 75, 'max': 150}},
                'Grade 2': {'Platelet': {'min': 50, 'max': 74.9}},
                'Grade 3': {'Platelet': {'min': 25, 'max': 49}},
                'Grade 4': {'Platelet': {'max': 24.9}}
            },
            'Anemia': {
                'Grade 1': {'Hemoglobin': {'min': 10, 'max': 12.6}},
                'Grade 2': {'Hemoglobin': {'min': 8, 'max': 9.9}},
                'Grade 3': {'Hemoglobin': {'min': 6.1, 'max': 7.9}},
                'Grade 4': {'Hemoglobin': {'max': 6}}
            },
            'Leukopenia': {
                'Grade 1': {'WBC': {'min': 3, 'max': 3.4}},
                'Grade 2': {'WBC': {'min': 2, 'max': 2.9}},
                'Grade 3': {'WBC': {'min': 1, 'max': 1.9}},
                'Grade 4': {'WBC': {'max': 0.9}}
            },
            'Neutropenia': {
                'Grade 1': {'ANC': {'min': 1.5, 'max': 7.0}},
                'Grade 2': {'ANC': {'min': 1, 'max': 1.4}},
                'Grade 3': {'ANC': {'min': 0.5, 'max': 0.99}},
                'Grade 4': {'ANC': {'min': 0, 'max': 0.49}},
            },
            'Renal Toxicity': {
                'Creatinine Clearance': {'Creatinine Clearance': {'max': 39.9}},
                '40% Change from Baseline': {'Baseline Creatinine Clearance': {}, 'Creatinine Clearance': {}},
            },
            'Hepatotoxicity': {
                'Bilirubinemia': {'Bilirubin': {'min': 3.00}},
                'Hypoalbuminemia': {'Albumin': {'min': 3},'INR':{'min': 1.5}}
            }
        },


        'Pluvicto': {
            'Myelosuppression': {
                'Grade 2': {'ANC': {'min': 1, 'max': 1.4}, 'Hemoglobin': {'min': 8, 'max': 9.9},'WBC': {'min': 2, 'max': 2.9},'Platelet': {'min': 50, 'max': 74.9}},
                'Grade ≥ 3': {'ANC': {'min': 0.0, 'max': 0.99},'Hemoglobin': {'min': 0, 'max': 7.9},'WBC': {'min': 0, 'max': 1.9},'Platelet': {'min': 0, 'max': 49}}
            },
            'Renal Toxicity': {
                'Grade ≥ 2 Creatinine Increase': {'Creatinine': {'min':3},'Baseline Creatinine Clearance': {}},
                'Creatinine Clearance': {'Creatinine Clearance': {}},
                '40% Creatinine Increase with >40% Clearance Decrease': {'Baseline Creatinine Clearance': {}, 'Creatinine Clearance': {}},
                'Grade ≥ 3': {'Grade ≥ 3':{}}
            },
            'Dry Mouth': {
                'Grade 2': {},
                'Grade 3': {}
            },
            'Gastrointestinal Toxicity': {
                'Grade ≥ 3': {}
            },
            'Hepatotoxicity': {
                'Grade 1': {'Bilirubin': {'max': 1.5}},  # ULN multiplier example
                'Grade 2': {'Bilirubin': {'min': 1.6, 'max': 3}},
                'Grade 3': {'Bilirubin': {'min': 3.1, 'max': 5}},
                'Grade 4': {'Bilirubin': {'min': 5.1}}
            }
        }
    }


    # Define dose modification guidance
    dose_modifications = {
        'Lutathera': {
            'Thrombocytopenia': {
                'Grade 2': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 2-4: Permanently discontinue LUTATHERA.',
                'Grade 3': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 2-4: Permanently discontinue LUTATHERA.',           
                'Grade 4': 'Withhold dose until resolution to Grade 0-1. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 2-4: Permanently discontinue LUTATHERA.'           
            },
            'Anemia': {
                'Grade 3': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 3-4: Permanently discontinue LUTATHERA.',
                'Grade 4': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 3-4: Permanently discontinue LUTATHERA.'
            },
            'Neutropenia': {
                'Grade 3': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 3-4: Permanently discontinue LUTATHERA.',
                'Grade 4': 'Withhold dose until resolution to Grade 0-2. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent Grade 3-4: Permanently discontinue LUTATHERA.'
            },
            'Renal Toxicity': {
                'Creatinine Clearance': 'Withhold dose until return to baseline. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent renal toxicity: Permanently discontinue LUTATHERA.',
                '40% Change from Baseline': 'Withhold dose until return to baseline. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent renal toxicity: Permanently discontinue LUTATHERA.'
            },
            'Hepatotoxicity': {
                'Grade 3 Bilirubinemia': ' Based on ULN as 1.0 g/L. \n\nWithhold dose until return to baseline. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent renal toxicity: Permanently discontinue LUTATHERA.',
                'Hypoalbuminemia': 'Withhold dose until return to baseline. Resume at 3.7 GBq if resolved. Return to 7.4 GBq if no recurrence. \n\n If recurrent renal toxicity: Permanently discontinue LUTATHERA.'
            },
            # Add more as needed
        },
        'Pluvicto': {
            'Myelosuppression': {
                'Grade 2': 'Withhold until improvement to Grade 1 or baseline.',
                'Grade ≥ 3': 'Withhold until improvement to Grade 1 or baseline, then reduce dose by 20%. \n\n If recurrent Grade ≥ 3, permanently discontinue PLUVICTO.'
            },
            'Renal Toxicity': {
                'Grade ≥ 2 Creatinine Increase': 'Withhold until improvement, or permanently discontinue if recurrent after dose reduction.',
                'Grade ≥ 3 Renal Toxicity': 'Permanently discontinue PLUVICTO.'

            },
            'Dry Mouth': {
                'Grade 2': 'Withhold PLUVICTO until improvement or return to baseline. Consider reducing PLUVICTO dose by 20% to 5.9 GBq (160 mCi).',
                'Grade 3': 'Withhold PLUVICTO until improvement or return to baseline. Reduce PLUVICTO dose by 20% to 5.9 GBq (160 mCi).',
                'Recurrent Grade 3': 'Permanently discontinue PLUVICTO.'
            },
            'Fatigue': {
                'Grade 2': 'Withhold PLUVICTO until improvement to Grade 1 or baseline.',
                'Grade 3': 'Withhold PLUVICTO until improvement to Grade 2 or baseline. Evaluate for supportive care.',
                'Grade 4': 'Withhold PLUVICTO until improvement to Grade 2 or baseline. Evaluate for supportive care.'
    },
            'AST/ALT Elevation': {
        'AST or ALT > 5x ULN without Liver Metastases': 'Permanently discontinue PLUVICTO due to severe AST or ALT elevation in the absence of liver metastases.',
    },
            # Add more as needed
        }
    }

    # Determine the adverse events and grades based on entered lab values
    def determine_events_and_grades(drug, lab_values):
        detected_events = []

        # Check which drug is selected
        if drug == "Lutathera":
            criteria = grading_criteria['Lutathera']
            
            for reaction, grades in criteria.items():
                for grade, limits in grades.items():
                    # Handle Renal Toxicity specific logic for Lutathera
                    if reaction == "Renal Toxicity" and grade == "40% Change from Baseline":
                        baseline = lab_values.get('Baseline Creatinine Clearance', None)
                        current = lab_values.get('Creatinine Clearance', None)
                        if baseline and current:
                            reduction = (abs(baseline - current) / baseline) * 100
                            if reduction >= 40:
                                detected_events.append((reaction, "40% Change from Baseline"))
                    elif reaction == "Renal Toxicity" and grade == "Creatinine Clearance":
                        current = lab_values.get('Creatinine Clearance', None)
                        if current is not None and current < 40:
                            detected_events.append((reaction, "Creatinine Clearance"))

                    # Handle Hepatotoxicity logic for Lutathera
                    elif reaction == "Hepatotoxicity" and grade == "Hypoalbuminemia":
                        bilirubin = lab_values.get('Bilirubin', None)
                        albumin = lab_values.get('Albumin', None)
                        inr = lab_values.get('INR', None)

                        if bilirubin is not None and bilirubin > 3:
                            detected_events.append((reaction, "Grade 3 Bilirubinemia"))
                        elif albumin is not None and inr is not None and albumin < 30 and inr > 1.5:
                            detected_events.append((reaction, "Hypoalbuminemia"))

                    # Regular grading criteria
                    else:
                        match = all(
                            lab in lab_values and (
                                ('min' not in thresholds or lab_values[lab] >= thresholds['min']) and
                                ('max' not in thresholds or lab_values[lab] <= thresholds['max'])
                            )
                            for lab, thresholds in limits.items()
                        )
                        if match:
                            detected_events.append((reaction, grade))

        elif drug == "Pluvicto":
            # Specific logic for Pluvicto
            baseline_creatinine = lab_values.get('Baseline Creatinine', None)
            current_creatinine = lab_values.get('Creatinine', None)
            baseline_cr_cl = lab_values.get('Baseline Creatinine Clearance', None)
            current_cr_cl = lab_values.get('Creatinine Clearance', None)
            uln_ast_alt=35

            # Check for Grade ≥ 2: Confirmed creatinine increase of 1.5x baseline or creatinine >= 3.3 mg/dL
            if baseline_creatinine and current_creatinine:
                if current_creatinine >= 1.5 * baseline_creatinine or current_creatinine >= 3.3:
                    detected_events.append(("Renal Toxicity", "Grade ≥ 2 Creatinine Increase"))
                    print("Creatinine increase detected")

            # Check for Grade ≥ 3: Creatinine > 3x baseline or > 3.3 mg/dL
            if baseline_creatinine and current_creatinine:
                if current_creatinine >= 3 * baseline_creatinine or current_creatinine > 3.3:
                    detected_events.append(("Renal Toxicity", "Grade ≥ 3 Renal Toxicity"))

            # Check for creatinine clearance < 30 mL/min
            if current_cr_cl is not None and current_cr_cl < 30:
                detected_events.append(("Renal Toxicity", "Confirmed Clearance < 30 mL/min"))

            # Check for >= 40% increase from baseline creatinine and >40% decrease from baseline clearance
            if baseline_creatinine and current_creatinine and baseline_cr_cl and current_cr_cl:
                creatinine_increase = (abs(current_creatinine - baseline_creatinine) / baseline_creatinine) * 100
                clearance_decrease = (abs(baseline_cr_cl - current_cr_cl) / baseline_cr_cl) * 100

                if creatinine_increase >= 40 and clearance_decrease > 40:
                    detected_events.append(("Renal Toxicity", "40% Creatinine Increase and >40% Clearance Decrease"))

            # Check for Dry Mouth
            dry_mouth_grade = lab_values.get("Dry Mouth Grade", None)
            if dry_mouth_grade:
                if dry_mouth_grade == 2:
                    detected_events.append(("Dry Mouth", "Grade 2"))
                elif dry_mouth_grade == 3:
                    detected_events.append(("Dry Mouth", "Grade 3"))

            # Check for Fatigue
            fatigue_grade = lab_values.get("Fatigue Grade", None)
            if fatigue_grade:
                if fatigue_grade == 3:
                    detected_events.append(("Fatigue", "Grade 3"))
                elif fatigue_grade == 4:
                    detected_events.append(("Fatigue", "Grade 4"))   

            # Check for AST/ALT elevation
            ast = lab_values.get("AST", None)
            alt = lab_values.get("ALT", None)
            uln_ast_alt = lab_values.get("ULN_AST_ALT", None)
            liver_metastases = lab_values.get("Liver Metastases", None)

            if ast is not None and alt is not None and uln_ast_alt:
                if liver_metastases == "No" and (ast > 5 * uln_ast_alt or alt > 5 * uln_ast_alt):
                    detected_events.append(("AST/ALT Elevation", "AST or ALT > 5x ULN without Liver Metastases"))


            # Regular grading criteria for Pluvicto
            criteria = grading_criteria['Pluvicto']
            for reaction, grades in criteria.items():
                for grade, limits in grades.items():
                    match = all(
                        lab in lab_values and (
                            ('min' not in thresholds or lab_values[lab] >= thresholds['min']) and
                            ('max' not in thresholds or lab_values[lab] <= thresholds['max'])
                        )
                        for lab, thresholds in limits.items()
                    )
                    if match:
                        detected_events.append((reaction, grade))
        else:
            st.warning(f"Drug '{drug}' not recognized in criteria.")

        return detected_events


    # Assess dose modification based on adverse event and grade
    def assess_dose_modification(drug, reaction, grade):
        modification = dose_modifications.get(drug, {}).get(reaction, {})
        for key in modification:
            if grade in key:
                return modification[key]
        return None  # Return None if no modification is required

    def save_to_csv(data, filename="analysis_results.csv"):
        # Convert data to DataFrame
        df = pd.DataFrame([data])
        # Append or create the file
        if os.path.exists(filename):
            df.to_csv(filename, mode='a', header=False, index=False)
        else:
            df.to_csv(filename, mode='w', header=True, index=False)

    # Streamlit app layout
    st.title("Radionuclide Therapy Dose Modification Assessment")
    st.write("Enter lab results to determine if an adverse event is present and receive corresponding dose modification guidance.")
    st. write("Criteria are based on CTCAE standardized grading scales and published FDA prescribing information. This application is for guidance only and all results should be independently verified.")

    # Drug selection
    drug = st.selectbox("Select Drug", options=['Lutathera', 'Pluvicto'])

    # Input fields for lab results
    if drug == 'Lutathera':
        lab_values = {}
        lab_values['Platelet'] = st.number_input("Platelet Count (µL)", min_value=0.0)
        lab_values['Hemoglobin'] = st.number_input("Hemoglobin (g/dL)", min_value=0.0)
        lab_values['WBC'] = st.number_input("White Blood Cell Count (WBC)(µL)", min_value=0.0)
        lab_values['ANC'] = st.number_input("Absolute Neutrophil Count (ANC) (µL)", min_value=0)
        lab_values['Creatinine Clearance'] = st.number_input("Creatinine Clearance (mL/min)", min_value=0.0)
        lab_values['Baseline Creatinine Clearance'] = st.number_input("Baseline Creatinine Clearance (mL/min)", min_value=0.0)
        lab_values['Bilirubin'] = st.number_input("Bilirubin (3x times ULN)", min_value=0.0)
        lab_values['Albumin']=st.number_input("Albumin (g/L)",min_value=0.0)
        lab_values['INR']=st.number_input("International Normalized Ratio (INR)",min_value=0.0)

    else: 

        lab_values = {}
        lab_values['Platelet'] = st.number_input("Platelet Count (µL)", min_value=0.0)
        lab_values['Hemoglobin'] = st.number_input("Hemoglobin (g/dL)", min_value=0.0)
        lab_values['WBC'] = st.number_input("White Blood Cell Count (WBC)(µL)", min_value=0.0)
        lab_values['ANC'] = st.number_input("Absolute Neutrophil Count (ANC) (µL)", min_value=0.0)
        lab_values['Baseline Creatinine']=st.number_input("Baseline Creatinine (mg/dL)",min_value=0.0)
        lab_values['Creatinine']=st.number_input("Creatinine (mg/dL)", min_value=0.0)
        lab_values['Creatinine Clearance'] = st.number_input("Creatinine Clearance (mL/min)", min_value=0.0)
        lab_values['Baseline Creatinine Clearance'] = st.number_input("Baseline Creatinine Clearance (mL/min)", min_value=0.0)
        lab_values['AST'] = st.number_input("AST", min_value=0.0)
        lab_values['ALT']= st.number_input("ALT",min_value=0.0)
        lab_values['Dry Mouth Grade'] = st.selectbox(
        "Dry Mouth Grade",
        options=[None, 1, 2, 3],
        format_func=lambda x: (
            "Select Grade"
            if x is None
            else f"Grade {x}: "
            + (
                "Symptomatic without significant dietary alteration; unstimulated saliva flow >0.2 ml/min"
                if x == 1
                else "Moderate symptoms; oral intake alterations; unstimulated saliva 0.1 to 0.2 ml/min"
                if x == 2
                else "Inability to adequately aliment orally; tube feeding or TPN indicated; unstimulated saliva <0.1 ml/min"
                if x == 3
                else 0
            )
        ),
    )
        lab_values['Fatigue Grade'] = st.selectbox(
        "Fatigue Grade",
        options=[None, 1, 2, 3],
        format_func=lambda x: (
            "Select Grade"
            if x is None
            else f"Grade {x}: "
            + (
                "Fatigue relieved by rest; does not interfere with daily living activities (ADLs)"
                if x == 1
                else "Fatigue that limits instrumental activities of daily living"
                if x == 2
                else "Fatigue that limits self-care activities of daily living"
                if x == 3
                else "Fatigue with life-threatening consequences" 
                if x== 4   
                else x   
            )
        ),
    )

        lab_values['Liver Metastases'] = st.selectbox("Presence of Liver Metastases?", options=["No", "Yes"])

    # Button to analyze lab values and determine adverse events
    if st.button("Analyze and Determine Dose Modification"):

            # Validation: Ensure all values are greater than zero
        if any(isinstance(value, (int, float)) and value <= 0 for value in lab_values.values()):
            st.error("All numeric values must be greater than zero. Please check your entries.")

        
        else:
            events = determine_events_and_grades(drug, lab_values)
            

            if events:
                entry = lab_values.copy()
                entry.update({"Detected Events": events})
                save_to_csv(entry)
            
            # Filter events that require dose modification
            events_with_modifications = [
                (reaction, grade, assess_dose_modification(drug, reaction, grade))
                for reaction, grade in events
                if assess_dose_modification(drug, reaction, grade) is not None
            ]
            
            if events_with_modifications:
                message=f"Detected {len(events_with_modifications)} Adverse Events Requiring {drug} Dose Modification Review"
                st.subheader(message)
                st.subheader(f"Please note hypersensitivty reactions and other adverse events outside of FDA prescribing information should be assessed independently")
                if drug=="Pluvicto":
                        st.write("Gastrointestinal toxicity should be assessed independently. Grade 3 or higher should withhold PLUVICTO until improvement to Grade 2 or Baseline. Subsequent doses should be reduced by 20% to 5.9 GBq (160 mCi). Recurrent Grade 3 or higher should permanently discontinue PLUVICTO.")
                for reaction, grade, next_steps in events_with_modifications:
                    st.write(f"Adverse Reaction: {reaction}")
                    st.write(f"Severity Grade/Reason: {grade}")
                    st.text("Dose Modification Guidance:")
                    st.text(next_steps)
                    st.write("---")
                    
            else:
                st.write("No adverse events requiring dose modification detected based on the entered lab values.")


