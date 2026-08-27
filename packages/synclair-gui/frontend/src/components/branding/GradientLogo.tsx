interface Props {
  onClick?: () => void;
  size?: "sm" | "lg";
}

export function GradientLogo({ onClick, size = "lg" }: Props) {
  return (
    <span
      onClick={onClick}
      //from-blue-600 via-purple-600 to-pink-500
      //from-pink-500 via-orange-500 to-yellow-500
      className={`${size === "lg" ? "text-2xl" : "text-xl"} font-extrabold tracking-tight bg-gradient-to-r from-purple-600 via-pik-600 to-amber-400 bg-clip-text text-transparent ${onClick ? "cursor-pointer hover:opacity-80 transition" : ""}`}
    >
      SynClair
    </span>
  );
}