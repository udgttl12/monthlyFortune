import Image from "next/image";

type YongyongMascotVariant = "hero" | "report" | "small";

type YongyongMascotProps = {
  readonly variant?: YongyongMascotVariant;
  readonly caption?: string;
};

export default function YongyongMascot({ variant = "small", caption }: YongyongMascotProps) {
  return (
    <figure className={`yongyong-mascot ${variant}`} aria-label="용용이 마스코트">
      <div className="yongyong-frame">
        <Image
          src="/yongyong-character-sheet.png"
          alt="별망토와 수정구슬을 든 용용이"
          width={1536}
          height={864}
          priority={variant === "hero"}
        />
      </div>
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}
