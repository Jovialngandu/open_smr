
import json
from pathlib import Path

from app.schemas.risk import (
    AssetContext,
    RiskAssessmentRequest,
)
from app.services.providers.gemini import GeminiProvider


CASES_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "risk_assessment_cases.json"
)


def main():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    provider = GeminiProvider()

    exact_likelihood = 0
    exact_impact = 0
    total_likelihood_error = 0
    total_impact_error = 0

    for case in cases:
        request = RiskAssessmentRequest(
            asset=AssetContext(
                name=case["asset_name"],
                category=case["category"],
                description=case["asset_description"],
                confidentiality=case["confidentiality"],
                integrity=case["integrity"],
                availability=case["availability"],
            ),
            threat_description=case["threat_description"],
        )

        try:
            result = provider.assess(request)

            likelihood_error = abs(
                result.likelihood - case["expected_likelihood"]
            )
            impact_error = abs(
                result.impact - case["expected_impact"]
            )

            total_likelihood_error += likelihood_error
            total_impact_error += impact_error

            exact_likelihood += likelihood_error == 0
            exact_impact += impact_error == 0

            print(
                f'{case["id"]}: '
                f'vraisemblance={result.likelihood} '
                f'(réf. {case["expected_likelihood"]}), '
                f'impact={result.impact} '
                f'(réf. {case["expected_impact"]})'
            )
            print(f"  Justification : {result.justification}")

        except Exception as exc:
            print(f'{case["id"]}: ERREUR — {exc}')

    count = len(cases)

    print("\n--- Résultats du benchmark ---")
    print(f"Scénarios : {count}")
    print(f"Vraisemblance exacte : {exact_likelihood}/{count}")
    print(f"Impact exact : {exact_impact}/{count}")
    print(
        "Erreur absolue moyenne vraisemblance : "
        f"{total_likelihood_error / count:.2f}"
    )
    print(
        "Erreur absolue moyenne impact : "
        f"{total_impact_error / count:.2f}"
    )


if __name__ == "__main__":
    main()