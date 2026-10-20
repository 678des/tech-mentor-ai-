import { useState } from "react";

export function SidebarGoals() {
  // 卒業年度（例: 2030年3月卒業）
  const [userGraduationYear] = useState<number>(2030);

  // 現在の年から動的に学年を計算するロジック
  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1; // 1-12
  const academicYear = currentMonth < 4 ? currentYear - 1 : currentYear;
  const entranceYear = userGraduationYear - 4;
  const calculatedGrade = academicYear - entranceYear + 1;
  const nowGrade = Math.min(Math.max(calculatedGrade, 1), 4);

  const [finalGoals, setFinalGoals] = useState<string>(
    "フルスタックエンジニアとして独立・活躍する",
  );
  const [firstGoals, setFirstGoals] = useState<string>(
    "ある程度のデザイン思考と、インフラを使ったポートフォリオを1作品作り上げる（Terraform + AWSなどの自動化、見やすいREADME）",
  );
  const [secondGoals, setSecondGoals] = useState<string>(
    "Wantedlyなどのアプリ開発インターン、または大学の少数精鋭インターンに合格して参加する",
  );
  const [thirdGoals, setThirdGoals] = useState<string>(
    "本命企業からの内定（内々定）を勝ち取る",
  );
  const [fourthGoals, setFourthGoals] = useState<string>(
    "独立できるレベルのビジネス知識とアプリケーション開発技術を身につける",
  );

  const gradeList = [
    {
      grade: 1,
      label: "1年生の目標",
      value: firstGoals,
      setter: setFirstGoals,
    },
    {
      grade: 2,
      label: "2年生の目標",
      value: secondGoals,
      setter: setSecondGoals,
    },
    {
      grade: 3,
      label: "3年生の目標",
      value: thirdGoals,
      setter: setThirdGoals,
    },
    {
      grade: 4,
      label: "4年生の目標",
      value: fourthGoals,
      setter: setFourthGoals,
    },
  ];

  return (
    <aside className="flex-1 w-48 p-4 bg-gray-100">
      <div>
        <h1>test</h1>
        {/* 最終目標 */}
        <div>
          <h3>🏆 最終目標</h3>
          <textarea
            rows={2}
            value={finalGoals}
            onChange={(e) => setFinalGoals(e.target.value)}
          />
        </div>

        {/* 各学年の目標一覧 */}
        <div>
          {gradeList.map((item) => {
            const isCurrent = item.grade === nowGrade;

            return (
              <div key={item.grade}>
                <h4>
                  {item.label}
                  {isCurrent && <span>📍 現在</span>}
                </h4>
                <textarea
                  rows={2}
                  value={item.value}
                  onChange={(e) => item.setter(e.target.value)}
                />
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
