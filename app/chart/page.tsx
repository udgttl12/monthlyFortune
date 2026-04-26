import { getCountryLabel, getDefaultTimezone } from "@/app/lib/locations";

const API_BASE_URL = process.env.MONTHLY_FORTUNE_API_URL ?? "http://127.0.0.1:8000";

interface ChartPageProps {
  searchParams: {
    birthDate?: string;
    birthTime?: string;
    city?: string;
    country?: string;
    timezone?: string;
    timeUnknown?: string;
  };
}

interface ChartPoint {
  name: string;
  longitude: number;
  sign: string;
  degree: number;
  minute: number;
  retrograde: boolean;
  house: number | null;
}

interface ChartAngle {
  longitude: number;
  sign: string;
  degree: number;
  minute: number;
}

interface ChartHouse {
  houseNumber: number;
  sign: string;
  cuspLongitude: number;
}

interface ChartAspect {
  pointA: string;
  pointB: string;
  aspect: string;
  orb: number;
  applying: boolean;
}

interface NatalChartResponse {
  points: ChartPoint[];
  angles: {
    asc: ChartAngle;
    mc: ChartAngle;
  };
  houses: ChartHouse[];
  aspects: ChartAspect[];
  location: {
    resolvedName: string;
    latitude: number;
    longitude: number;
    timezone: string;
    countryCode: string;
  };
}

function formatBirthDate(value?: string) {
  if (!value) {
    return "입력되지 않음";
  }

  return value.replaceAll("-", ".");
}

function formatBirthTime(value?: string, timeUnknown?: string) {
  if (!value) {
    return "입력되지 않음";
  }

  if (timeUnknown === "true") {
    return `${value} (정오 기준 임시값)`;
  }

  return value;
}

function formatDegree(sign: string, degree: number, minute: number) {
  return `${sign} ${String(degree).padStart(2, "0")}°${String(minute).padStart(2, "0")}′`;
}

function formatAspectDirection(applying: boolean) {
  return applying ? "정확각으로 접근 중" : "정확각을 지난 상태";
}

const CORE_POINT_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars"];

const POINT_LABELS: Record<string, string> = {
  Sun: "태양",
  Moon: "달",
  Mercury: "수성",
  Venus: "금성",
  Mars: "화성",
  Jupiter: "목성",
  Saturn: "토성",
  Uranus: "천왕성",
  Neptune: "해왕성",
  Pluto: "명왕성",
  "North Node": "북노드",
  Lilith: "릴리스",
  Chiron: "키론",
  Fortune: "포춘",
  Vertex: "버텍스",
  ASC: "ASC",
  MC: "MC",
  DSC: "DSC",
  IC: "IC"
};

async function getNatalChart(searchParams: ChartPageProps["searchParams"]): Promise<{
  data: NatalChartResponse | null;
  error: string | null;
}> {
  if (!searchParams.birthDate || !searchParams.birthTime || !searchParams.city || !searchParams.country) {
    return { data: null, error: "출생 정보가 충분하지 않아 차트를 계산할 수 없습니다." };
  }

  const params = new URLSearchParams({
    birthDate: searchParams.birthDate,
    birthTime: searchParams.birthTime,
    city: searchParams.city,
    countryCode: searchParams.country
  });

  if (searchParams.timezone) {
    params.set("timezone", searchParams.timezone);
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chart/natal?${params.toString()}`, {
      cache: "no-store"
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => null);
      const message = payload?.detail ?? "차트 계산 중 오류가 발생했습니다.";
      return { data: null, error: message };
    }

    return { data: await response.json(), error: null };
  } catch {
    return {
      data: null,
      error: "백엔드에 연결할 수 없습니다. FastAPI 서버가 127.0.0.1:8000 에서 실행 중인지 확인해 주세요."
    };
  }
}

export default async function ChartPage({ searchParams }: ChartPageProps) {
  const countryLabel = getCountryLabel(searchParams.country);
  const fallbackTimezone = searchParams.timezone ?? getDefaultTimezone(searchParams.country);
  const { data, error } = await getNatalChart(searchParams);
  const isTimeEstimated = searchParams.timeUnknown === "true";
  const primaryPoints = data?.points.filter((point) => CORE_POINT_ORDER.includes(point.name)) ?? [];
  const highlightedAspects = data?.aspects.slice(0, 8) ?? [];

  return (
    <div className="stack">
      <section className="card">
        <h1>출생 차트 결과</h1>
        <p className="muted">
          실제 천문 계산 결과를 먼저 핵심값 중심으로 요약해 보여드리고, 전체 세부값은 아래에서
          펼쳐볼 수 있습니다.
        </p>
      </section>

      <section className="card">
        <div className="details-grid">
          <p>
            <strong>생년월일:</strong> {formatBirthDate(searchParams.birthDate)}
          </p>
          <p>
            <strong>출생 시간:</strong> {formatBirthTime(searchParams.birthTime, searchParams.timeUnknown)}
          </p>
          <p>
            <strong>국가:</strong> {countryLabel}
          </p>
          <p>
            <strong>입력 도시:</strong> {searchParams.city ?? "입력되지 않음"}
          </p>
          <p>
            <strong>입력 timezone:</strong> {fallbackTimezone}
          </p>
        </div>
      </section>

      {isTimeEstimated ? (
        <section className="card warning-card">
          <h2>출생 시간이 임시값입니다</h2>
          <p>
            지금 결과는 <strong>정오 12:00</strong> 기준 임시 계산입니다. 이 경우 ASC, 하우스,
            포춘, 버텍스는 실제 값과 크게 달라질 수 있으니 참고용으로만 봐 주세요.
          </p>
        </section>
      ) : null}

      {error ? (
        <section className="card info-card">
          <h2>계산 오류</h2>
          <p>{error}</p>
        </section>
      ) : null}

      {data ? (
        <>
          <section className="card">
            <div className="chart-meta-grid">
              <article className="metric-card">
                <h2>ASC</h2>
                <p>{formatDegree(data.angles.asc.sign, data.angles.asc.degree, data.angles.asc.minute)}</p>
                <span className="metric-note">겉으로 보이는 인상과 접근 방식</span>
              </article>
              <article className="metric-card">
                <h2>MC</h2>
                <p>{formatDegree(data.angles.mc.sign, data.angles.mc.degree, data.angles.mc.minute)}</p>
                <span className="metric-note">사회적 방향성과 커리어 축</span>
              </article>
              <article className="metric-card">
                <h2>확정된 위치</h2>
                <p>{data.location.resolvedName}</p>
                <span className="metric-note">{data.location.timezone}</span>
              </article>
              <article className="metric-card">
                <h2>좌표</h2>
                <p>
                  {data.location.latitude.toFixed(4)}, {data.location.longitude.toFixed(4)}
                </p>
                <span className="metric-note">도시 해석에 사용된 기준 좌표</span>
              </article>
            </div>
          </section>

          <section className="section-grid two-column-grid">
            <article className="card section-card">
              <h2>핵심 포인트 요약</h2>
              <div className="reading-list">
                {primaryPoints.map((point) => (
                  <p key={point.name}>
                    <strong>{POINT_LABELS[point.name] ?? point.name}</strong>:{" "}
                    {formatDegree(point.sign, point.degree, point.minute)}
                    {point.house ? ` · ${point.house}H` : ""}
                    {point.retrograde ? " · R" : ""}
                  </p>
                ))}
              </div>
            </article>

            <article className="card section-card">
              <h2>가장 가까운 어스펙트</h2>
              <div className="reading-list">
                {highlightedAspects.map((aspect) => (
                  <p key={`${aspect.pointA}-${aspect.pointB}-${aspect.aspect}`}>
                    <strong>
                      {POINT_LABELS[aspect.pointA] ?? aspect.pointA} {aspect.aspect}{" "}
                      {POINT_LABELS[aspect.pointB] ?? aspect.pointB}
                    </strong>
                    : Orb {aspect.orb.toFixed(2)}° · {formatAspectDirection(aspect.applying)}
                  </p>
                ))}
              </div>
            </article>
          </section>

          <section className="stack compact-stack">
            <details className="card disclosure-card" open>
              <summary>전체 행성 및 포인트 보기</summary>
              <div className="reading-list disclosure-body">
                {data.points.map((point) => (
                  <p key={point.name}>
                    <strong>{POINT_LABELS[point.name] ?? point.name}</strong>:{" "}
                    {formatDegree(point.sign, point.degree, point.minute)}
                    {point.house ? ` · ${point.house}H` : ""}
                    {point.retrograde ? " · 역행" : ""}
                  </p>
                ))}
              </div>
            </details>

            <details className="card disclosure-card">
              <summary>홀사인 하우스 전체 보기</summary>
              <div className="reading-list disclosure-body">
                {data.houses.map((house) => (
                  <p key={house.houseNumber}>
                    <strong>{house.houseNumber}하우스</strong>: {house.sign} 0°00′
                  </p>
                ))}
              </div>
            </details>

            <details className="card disclosure-card">
              <summary>어스펙트 전체 보기</summary>
              <div className="reading-list disclosure-body">
                {data.aspects.map((aspect) => (
                  <p key={`${aspect.pointA}-${aspect.pointB}-${aspect.aspect}`}>
                    <strong>
                      {POINT_LABELS[aspect.pointA] ?? aspect.pointA} {aspect.aspect}{" "}
                      {POINT_LABELS[aspect.pointB] ?? aspect.pointB}
                    </strong>
                    : Orb {aspect.orb.toFixed(2)}° · {formatAspectDirection(aspect.applying)}
                  </p>
                ))}
              </div>
            </details>
          </section>
        </>
      ) : null}
    </div>
  );
}
