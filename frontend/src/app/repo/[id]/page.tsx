import { notFound } from "next/navigation";
import { fetchRepository } from "@/lib/api";
import { RepoHeader } from "@/components/detail/RepoHeader";
import { IntelligenceSection } from "@/components/detail/IntelligenceSection";
import { QuickStartTutorial } from "@/components/detail/QuickStartTutorial";
import { MentalModel } from "@/components/detail/MentalModel";
import { PracticalRecipe } from "@/components/detail/PracticalRecipe";
import { LearningPath } from "@/components/detail/LearningPath";
import { ExternalLinks } from "@/components/detail/ExternalLinks";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function RepoDetailPage({ params }: PageProps) {
  const { id } = await params;
  const repoId = parseInt(id, 10);
  if (Number.isNaN(repoId)) notFound();
  let repo;
  try {
    repo = await fetchRepository(repoId);
  } catch {
    notFound();
  }

  return (
    <article className="mx-auto max-w-4xl space-y-10">
      <RepoHeader repo={repo} />
      <IntelligenceSection content={repo.content.what_and_why} />
      <QuickStartTutorial content={repo.content.quick_start} />
      <MentalModel content={repo.content.mental_model} />
      <PracticalRecipe content={repo.content.practical_recipe} />
      <LearningPath content={repo.content.learning_path} />
      <ExternalLinks repo={repo} />
    </article>
  );
}
